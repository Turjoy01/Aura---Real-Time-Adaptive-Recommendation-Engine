from src.db.mongodb import get_collection
from typing import List, Dict, Any
from datetime import datetime, timedelta

class ColdStartEngine:
    """Handles cold-start recommendation for new users"""
    
    @staticmethod
    async def get_recommendations(
        user_id: str,
        lat: float,
        lng: float,
        radius_km: float = 25.0,
        count: int = 30,
        onboarding_intent: str = "explore"
    ) -> List[Dict[str, Any]]:
        """
        Get smart cold-start recommendations blending 4 signals:
        1. Popular events in user's current city/neighborhood (40%)
        2. Trending events among same age group (25%)
        3. Matches onboarding intent (20%)
        4. Current time/day patterns of the city (15%)
        """
        
        recommendations = []
        
        # Get user profile
        profile_collection = await get_collection("user_preference_profile")
        user_profile = await profile_collection.find_one({"user_id": user_id})
        
        if not user_profile:
            user_profile = {}
        
        # Signal 1: Popular events in area (40% weight)
        popular_events = await ColdStartEngine._get_popular_in_area(lat, lng, radius_km, count // 2)
        for event in popular_events:
            event["cold_start_score"] = event.get("popularity_score", 0.5) * 0.4
        recommendations.extend(popular_events)
        
        # Signal 2: Trending among age group (25% weight)
        age = user_profile.get("age", 25)
        trending_events = await ColdStartEngine._get_trending_by_age(age, lat, lng, radius_km, count // 3)
        for event in trending_events:
            event["cold_start_score"] = event.get("trending_score", 0.6) * 0.25
        recommendations.extend(trending_events)
        
        # Signal 3: Intent-based (20% weight)
        intent_events = await ColdStartEngine._get_intent_based_events(
            onboarding_intent, 
            lat, 
            lng, 
            radius_km, 
            count // 4
        )
        for event in intent_events:
            event["cold_start_score"] = 0.7 * 0.2
        recommendations.extend(intent_events)
        
        # Signal 4: Time/day patterns (15% weight)
        time_events = await ColdStartEngine._get_time_pattern_events(lat, lng, radius_km, count // 4)
        for event in time_events:
            event["cold_start_score"] = 0.6 * 0.15
        recommendations.extend(time_events)
        
        # Deduplicate and sort by composite score
        seen_ids = set()
        unique_recommendations = []
        for event in recommendations:
            if event.get("event_id") not in seen_ids:
                seen_ids.add(event.get("event_id"))
                unique_recommendations.append(event)
        
        unique_recommendations.sort(
            key=lambda x: x.get("cold_start_score", 0),
            reverse=True
        )
        
        return unique_recommendations[:count]
    
    @staticmethod
    async def _get_popular_in_area(
        lat: float,
        lng: float,
        radius_km: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get popular events within radius"""
        collection = await get_collection("events")
        # Mock data - in production: query actual events with geospatial index
        return await collection.find({
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]
                    },
                    "$maxDistance": radius_km * 1000
                }
            }
        }).sort("popularity_score", -1).limit(limit).to_list(limit)
    
    @staticmethod
    async def _get_trending_by_age(
        age: int,
        lat: float,
        lng: float,
        radius_km: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get trending events for age group"""
        collection = await get_collection("events")
        # Mock - query events trending with target age group
        return await collection.find({
            "trending_age_range": {"$gte": age - 3, "$lte": age + 3}
        }).sort("trending_score", -1).limit(limit).to_list(limit)
    
    @staticmethod
    async def _get_intent_based_events(
        intent: str,
        lat: float,
        lng: float,
        radius_km: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get events matching onboarding intent"""
        collection = await get_collection("events")
        
        intent_mapping = {
            "explore": ["diverse_category"],
            "create": ["large_scale", "production_event"],
            "freelance": ["industry_networking", "professional_event"]
        }
        
        categories = intent_mapping.get(intent, ["diverse_category"])
        return await collection.find({
            "category": {"$in": categories}
        }).limit(limit).to_list(limit)
    
    @staticmethod
    async def _get_time_pattern_events(
        lat: float,
        lng: float,
        radius_km: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get events matching current time patterns"""
        collection = await get_collection("events")
        current_hour = datetime.utcnow().hour
        current_day = datetime.utcnow().strftime("%A")
        
        # Peak hours: late night (Thu-Sat), evening (all days)
        return await collection.find({
            "day_of_week": current_day
        }).sort("popularity_score", -1).limit(limit).to_list(limit)
