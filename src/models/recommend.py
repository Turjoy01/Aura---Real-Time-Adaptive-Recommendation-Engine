from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class LocationModel(BaseModel):
    lat: float
    lng: float

class RecommendFeedRequest(BaseModel):
    """Request for personalized feed"""
    lat: float
    lng: float
    radius_km: float = 25.0
    count: int = Field(30, ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 40.71,
                "lng": -73.95,
                "radius_km": 25,
                "count": 30
            }
        }

class EventRecommendation(BaseModel):
    """Single event recommendation"""
    event_id: str
    score: float = Field(..., ge=0, le=1)
    reason: str = Field(..., description="Why this event was recommended")

class RecommendFeedResponse(BaseModel):
    """Feed recommendation response"""
    events: List[EventRecommendation]
    total_count: int

class NaturalQueryRequest(BaseModel):
    """Natural language query for events"""
    query: str = Field(..., min_length=3)
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "best hip hop in bushwick tonight under $40",
                "lat": 40.71,
                "lng": -73.95
            }
        }

class ParsedIntent(BaseModel):
    """Parsed user intent from NLP"""
    categories: List[str]
    price_max: Optional[float] = None
    time_slot: Optional[str] = None
    location: Optional[str] = None
    age_restriction: Optional[str] = None
    vibe_keywords: List[str] = Field(default_factory=list)

class NaturalQueryResponse(BaseModel):
    """Response to natural language query"""
    parsed_intent: ParsedIntent
    events: List[EventRecommendation]
    explanation: str

class HighlightsRequest(BaseModel):
    """Request for highlights row"""
    lat: float
    lng: float
    radius_km: float = 25.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 40.71,
                "lng": -73.95,
                "radius_km": 25
            }
        }

class HighlightsResponse(BaseModel):
    """Highlights response"""
    event_ids: List[str]
    message: str

class RewardRequest(BaseModel):
    """Reinforcement learning reward feedback"""
    event_id: str
    reward: float = Field(..., ge=-1.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "507f1f77bcf86cd799439011",
                "reward": 1.0
            }
        }
