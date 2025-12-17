from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BehaviorType(str, Enum):
    SEARCH = "search"
    VIEW_EVENT = "view_event"
    LIKE = "like"
    REPOST = "repost"
    PURCHASE = "purchase"
    ATTEND = "attend"
    SKIP = "skip"
    NATURAL_QUERY = "natural_query"
    OPEN_APP = "open_app"

class LocationModel(BaseModel):
    lat: float
    lng: float

class FiltersModel(BaseModel):
    category: Optional[str] = None
    price_max: Optional[float] = None
    time: Optional[str] = None
    radius_km: Optional[float] = None
    age_restriction: Optional[str] = None

class BehaviorLogRequest(BaseModel):
    """Request model for logging user behavior"""
    type: BehaviorType
    event_id: Optional[str] = None
    query_text: Optional[str] = None
    filters_applied: Optional[FiltersModel] = None
    location: Optional[LocationModel] = None
    chosen_event_ids: Optional[List[str]] = None
    session_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "purchase",
                "event_id": "507f1f77bcf86cd799439011",
                "location": {"lat": 40.7128, "lng": -74.0060},
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

class BehaviorEventDB(BaseModel):
    """MongoDB document model for behavior events"""
    user_id: str
    type: BehaviorType
    event_id: Optional[str] = None
    query_text: Optional[str] = None
    filters_applied: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, float]] = None
    chosen_event_ids: Optional[List[str]] = None
    session_id: str
    reward: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
