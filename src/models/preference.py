from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class IntentType(str, Enum):
    EXPLORE = "explore"
    CREATE = "create"
    FREELANCE = "freelance"

class GenderType(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class CategoryScore(BaseModel):
    name: str
    score: float

class PriceRange(BaseModel):
    avg: Optional[float] = None
    max_ever_paid: Optional[float] = None
    sweet_spot_min: Optional[float] = None
    sweet_spot_max: Optional[float] = None

class LocationPreference(BaseModel):
    city: str
    neighborhood: Optional[str] = None
    score: float

class UserPreferenceProfile(BaseModel):
    """User preference profile document"""
    user_id: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    onboarding_intent: Optional[IntentType] = None
    age: Optional[int] = None
    gender: Optional[GenderType] = None
    preferred_categories: List[CategoryScore] = Field(default_factory=list)
    preferred_price_range: Optional[PriceRange] = None
    preferred_time_slots: List[str] = Field(default_factory=list)
    preferred_days: List[str] = Field(default_factory=list)
    preferred_locations: List[LocationPreference] = Field(default_factory=list)
    total_events_attended: int = 0
    cold_start_completed: bool = False
    embedding_vector: Optional[List[float]] = None

class OnboardingRequest(BaseModel):
    """Onboarding data from user"""
    intent: IntentType
    age: int
    gender: GenderType
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "explore",
                "age": 24,
                "gender": "female"
            }
        }
