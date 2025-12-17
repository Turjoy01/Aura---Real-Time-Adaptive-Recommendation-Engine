from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.core.security import security, verify_token
from src.models.behavior import BehaviorLogRequest, BehaviorEventDB
from src.db.mongodb import get_collection
from src.services.preference_updater import PreferenceUpdater
from datetime import datetime

router = APIRouter(
    prefix="/v1/behavior",
    tags=["Behavior Logging"],
    responses={
        401: {"description": "Unauthorized - invalid token"},
        500: {"description": "Internal server error"}
    }
)

@router.post(
    "/log",
    status_code=201,
    summary="Log User Behavior Event",
    description="Log every user action (search, view, like, purchase, etc). This is the heartbeat of the learning system.",
    response_description="Event logged successfully"
)
async def log_behavior(
    request: BehaviorLogRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Log user behavior for real-time learning
    
    **Signals tracked:**
    - Purchase/Attendance: +1.0 reward (strongest signal)
    - Likes/Reposts/Views: positive signal
    - Searches: filter preferences
    - Natural queries: intent extraction
    - Skips: negative signal
    
    **Used for:**
    - Updating user preference profiles
    - Training reinforcement learning models
    - Improving personalization in real-time
    """
    try:
        user_id = verify_token(credentials)
        
        # Create behavior event document
        behavior_event = {
            "user_id": user_id,
            "type": request.type.value,
            "event_id": request.event_id,
            "query_text": request.query_text,
            "filters_applied": request.filters_applied.dict() if request.filters_applied else None,
            "location": request.location.dict() if request.location else None,
            "chosen_event_ids": request.chosen_event_ids,
            "session_id": request.session_id,
            "reward": None,
            "timestamp": datetime.utcnow()
        }
        
        # Store in MongoDB
        collection = await get_collection("user_behavior_events")
        result = await collection.insert_one(behavior_event)
        
        # Update user preferences in real-time (no batch jobs!)
        event_data = None
        if request.event_id:
            event_collection = await get_collection("events")
            event_data = await event_collection.find_one({"_id": request.event_id})
        
        await PreferenceUpdater.update_from_behavior(
            user_id=user_id,
            behavior_type=request.type.value,
            event_data=event_data
        )
        
        return {
            "status": "success",
            "message": "Behavior logged successfully",
            "event_id": str(result.inserted_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging behavior: {str(e)}"
        )
