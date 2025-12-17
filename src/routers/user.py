from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from src.core.security import security, verify_token
from src.models.preference import OnboardingRequest, UserPreferenceProfile
from src.db.mongodb import get_collection
from datetime import datetime

router = APIRouter(
    prefix="/v1/user",
    tags=["User Management"],
    responses={
        401: {"description": "Unauthorized - invalid token"},
        500: {"description": "Internal server error"}
    }
)

@router.post(
    "/onboarding",
    status_code=200,
    summary="Submit Onboarding Data",
    description="Complete onboarding by submitting intent, age, and gender",
    response_description="Onboarding data saved"
)
async def submit_onboarding(
    request: OnboardingRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    **Complete user onboarding**
    
    Collects initial preferences:
    - **Intent**: explore (diverse events), create (big events), freelance (industry)
    - **Age**: for demographic-based recommendations
    - **Gender**: for personalized filtering (optional)
    
    Used in cold-start recommendations
    """
    try:
        user_id = verify_token(credentials)
        
        # Get or create preference profile
        collection = await get_collection("user_preference_profile")
        
        profile = {
            "user_id": user_id,
            "onboarding_intent": request.intent.value,
            "age": request.age,
            "gender": request.gender.value,
            "updated_at": datetime.utcnow(),
            "preferred_categories": [],
            "preferred_locations": [],
            "total_events_attended": 0,
            "cold_start_completed": False
        }
        
        await collection.update_one(
            {"user_id": user_id},
            {"$set": profile},
            upsert=True
        )
        
        return {
            "status": "success",
            "message": "Onboarding completed",
            "user_id": user_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing onboarding: {str(e)}"
        )

@router.get(
    "/profile",
    response_model=dict,
    summary="Get User Preference Profile",
    description="Debug endpoint - view current preference vector and all learned preferences"
)
async def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    **Debug endpoint** - See your complete preference profile
    
    Returns:
    - Onboarding data (intent, age, gender)
    - Learned category preferences
    - Price range preferences
    - Location preferences
    - Attendance history
    - Cold start status
    - Embedding vector (if applicable)
    """
    try:
        user_id = verify_token(credentials)
        
        collection = await get_collection("user_preference_profile")
        profile = await collection.find_one({"user_id": user_id})
        
        if not profile:
            return {
                "status": "not_found",
                "message": "No preference profile yet",
                "user_id": user_id
            }
        
        # Remove MongoDB _id from response
        profile.pop("_id", None)
        
        return {
            "status": "success",
            "profile": profile
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching profile: {str(e)}"
        )

@router.post(
    "/reset",
    summary="Reset User Profile",
    description="Delete preference profile to restart cold-start phase"
)
async def reset_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    **Reset Profile**
    
    Deletes the user's preference profile to simulate a fresh user state.
    Useful for testing cold-start vs. personalized recommendations.
    """
    try:
        user_id = verify_token(credentials)
        collection = await get_collection("user_preference_profile")
        result = await collection.delete_one({"user_id": user_id})
        
        return {
            "status": "success",
            "message": "Profile reset successfully",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting profile: {str(e)}"
        )
