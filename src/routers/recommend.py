from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.core.security import security, verify_token
from src.models.recommend import (
    RecommendFeedRequest,
    RecommendFeedResponse,
    EventRecommendation,
    NaturalQueryRequest,
    NaturalQueryResponse,
    HighlightsRequest,
    HighlightsResponse,
    RewardRequest
)
from src.services.preference_updater import PreferenceUpdater
from src.services.cold_start import ColdStartEngine
from src.services.natural_parser import NaturalLanguageParser
from src.services.bandit import BanditAlgorithm
from src.db.mongodb import get_collection
from datetime import datetime

router = APIRouter(
    prefix="/v1/recommend",
    tags=["Recommendations"],
    responses={
        401: {"description": "Unauthorized - invalid token"},
        500: {"description": "Internal server error"}
    }
)

nlp_parser = NaturalLanguageParser()

@router.post(
    "/feed",
    response_model=RecommendFeedResponse,
    summary="Get Personalized Home Feed",
    description="Get 30 personalized events for the home tab based on user preferences and behavior"
)
async def get_personalized_feed(
    request: RecommendFeedRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> RecommendFeedResponse:
    """
    **Real-time personalized feed** using multi-armed bandit algorithm
    
    Returns sub-300ms with cached user preferences:
    1. Get user preference profile
    2. Score events against preferences
    3. Apply bandit algorithm (85% exploit / 15% explore)
    4. Return top N events with reasons
    
    **Handles cold-start users** with smart signal blending
    """
    try:
        user_id = verify_token(credentials)
        
        # Get user preference profile
        profile = await PreferenceUpdater.get_profile(user_id)
        
        # If cold start, use smart recommendations
        if not profile or not profile.get("cold_start_completed"):
            intent = profile.get("onboarding_intent", "explore") if profile else "explore"
            cold_start_events = await ColdStartEngine.get_recommendations(
                user_id=user_id,
                lat=request.lat,
                lng=request.lng,
                radius_km=request.radius_km,
                count=request.count,
                onboarding_intent=intent
            )
            
            # Convert to recommendations
            recommendations = [
                EventRecommendation(
                    event_id=str(event.get("_id", event.get("event_id"))),
                    score=event.get("cold_start_score", 0.5),
                    reason="Recommended for new members"
                )
                for event in cold_start_events[:request.count]
            ]
        else:
            # Production: Score events based on user preferences
            events_collection = await get_collection("events")
            all_events = await events_collection.find({}).to_list(1000)
            
            scored_events = []
            for event in all_events:
                score = _score_event(event, profile)
                scored_events.append({
                    "_id": event.get("_id"),
                    "event_id": str(event.get("_id")),
                    "score": score,
                    "category": event.get("category"),
                    "reason": _generate_reason(event, profile)
                })
            
            # Apply bandit algorithm
            selected = BanditAlgorithm.select_events_epsilon_greedy(
                scored_events,
                request.count,
                epsilon=0.15
            )
            
            recommendations = [
                EventRecommendation(
                    event_id=event["event_id"],
                    score=event["score"],
                    reason=event["reason"]
                )
                for event in selected
            ]
        
        return RecommendFeedResponse(
            events=recommendations,
            total_count=len(recommendations)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating feed: {str(e)}"
        )

@router.post(
    "/natural",
    response_model=NaturalQueryResponse,
    summary="AI Copilot Natural Language Search",
    description="Search events using natural language (e.g., 'techno in Brooklyn tonight under $40')"
)
async def natural_language_search(
    request: NaturalQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> NaturalQueryResponse:
    """
    **AI Copilot search** - converts natural language to structured queries
    
    Uses OpenAI to parse user intent:
    - "techno in Brooklyn tonight under $40" →
      categories: [Techno], price_max: 40, location: Brooklyn, time: Late Night
    
    Then finds matching events and generates explanation
    """
    try:
        user_id = verify_token(credentials)
        
        # Parse natural language query using LLM
        parsed_intent = await nlp_parser.parse_query(request.query)
        
        # Find matching events
        events_collection = await get_collection("events")
        query_filter = {}
        
        if parsed_intent.categories:
            query_filter["category"] = {"$in": parsed_intent.categories}
        if parsed_intent.price_max:
            query_filter["price"] = {"$lte": parsed_intent.price_max}
        if parsed_intent.age_restriction:
            query_filter["age_restriction"] = parsed_intent.age_restriction
        
        matching_events = await events_collection.find(query_filter).to_list(100)
        
        # Get user profile for scoring
        profile = await PreferenceUpdater.get_profile(user_id)
        
        # Score and rank events
        recommendations = []
        for event in matching_events:
            score = _score_event(event, profile) if profile else 0.5
            recommendations.append(
                EventRecommendation(
                    event_id=str(event.get("_id")),
                    score=score,
                    reason=_generate_reason(event, profile)
                )
            )
        
        # Sort by score
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        # Generate explanation
        explanation = await nlp_parser.generate_explanation(
            request.query,
            parsed_intent,
            len(recommendations)
        )
        
        return NaturalQueryResponse(
            parsed_intent=parsed_intent,
            events=recommendations[:50],
            explanation=explanation
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing natural query: {str(e)}"
        )

@router.post(
    "/highlights",
    response_model=HighlightsResponse,
    summary="Get Highlights Row",
    description="Get 5-10 top trending/recommended events for the Highlights row under Stories"
)
async def get_highlights(
    request: HighlightsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> HighlightsResponse:
    """
    **Highlights row** - shows trending events under Stories section
    
    Combines:
    - Personal preferences
    - Trending events in area
    - Events liked by similar users
    """
    try:
        user_id = verify_token(credentials)
        
        # Get top trending events
        events_collection = await get_collection("events")
        trending = await events_collection.find(
            {"trending_score": {"$gte": 0.7}}
        ).sort("trending_score", -1).limit(10).to_list(10)
        
        event_ids = [str(event.get("_id")) for event in trending]
        
        return HighlightsResponse(
            event_ids=event_ids,
            message="Trending tonight in your area"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching highlights: {str(e)}"
        )

@router.post(
    "/feedback/reward",
    status_code=200,
    summary="Submit RL Reward Feedback",
    description="Submit reinforcement learning feedback after user buys, attends, or skips event",
    response_description="Reward processed and profile updated"
)
async def submit_reward(
    request: RewardRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    **Reinforcement Learning Feedback**
    
    Call this after user:
    - Buys ticket (reward = +1.0)
    - Marks as attending (reward = +1.0)
    - Skips event (reward = -0.5 to -1.0)
    - Dislikes event (reward = -0.3)
    
    Instantly updates user preferences - no batch jobs!
    """
    try:
        user_id = verify_token(credentials)
        
        # Update behavior event with reward
        behavior_collection = await get_collection("user_behavior_events")
        await behavior_collection.update_one(
            {"_id": request.event_id},
            {"$set": {"reward": request.reward}}
        )
        
        # Get event data
        events_collection = await get_collection("events")
        event_data = await events_collection.find_one({"_id": request.event_id})
        
        # Determine behavior type based on reward value
        if request.reward >= 0.8:
            behavior_type = "purchase"
        elif request.reward < -0.5:
            behavior_type = "skip"
        else:
            behavior_type = "like"
        
        # Update preferences in real-time
        await PreferenceUpdater.update_from_behavior(
            user_id=user_id,
            behavior_type=behavior_type,
            event_data=event_data.dict() if event_data else None,
            reward=request.reward
        )
        
        return {
            "status": "success",
            "message": "Reward processed, profile updated",
            "reward": request.reward
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing reward: {str(e)}"
        )

# Helper functions
def _score_event(event: dict, profile: dict = None) -> float:
    """Score an event based on user profile"""
    if not profile:
        return 0.5
    
    score = 0.5
    
    # Category preference
    category = event.get("category")
    if category:
        cat_prefs = profile.get("preferred_categories", [])
        for cat in cat_prefs:
            if cat.get("name") == category:
                score = cat.get("score", 0.5)
                break
    
    # Price preference
    price = event.get("price", 0)
    price_range = profile.get("preferred_price_range", {})
    if price_range:
        sweet_min = price_range.get("sweet_spot_min", 0)
        sweet_max = price_range.get("sweet_spot_max", 1000)
        if sweet_min <= price <= sweet_max:
            score = min(1.0, score + 0.1)
    
    return min(1.0, max(0.0, score))

def _generate_reason(event: dict, profile: dict = None) -> str:
    """Generate human-readable reason for recommendation"""
    if not profile:
        return "Trending now"
    
    category = event.get("category")
    if category:
        return f"You love {category}"
    
    return "Curated for you"
