"""
AI Engine Schemas
Pydantic models for AI decision outputs
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone


class PrefetchItem(BaseModel):
    """Prefetch decision item"""
    content_id: str = Field(..., description="Content ID to prefetch")
    target_edges: List[str] = Field(..., description="Edge IDs to prefetch to")
    ttl_seconds: int = Field(..., ge=60, le=86400, description="TTL in seconds (60-86400)")
    priority: int = Field(..., ge=0, le=100, description="Priority score (0-100)")


class EvictionItem(BaseModel):
    """Eviction decision item"""
    edge_id: str = Field(..., description="Edge ID to evict from")
    content_id: str = Field(..., description="Content ID to evict")
    reason: str = Field(..., description="Reason for eviction")
    priority: int = Field(..., ge=0, le=100, description="Priority score (0-100)")


class TTLUpdateItem(BaseModel):
    """TTL update decision item"""
    edge_id: str = Field(..., description="Edge ID")
    content_id: str = Field(..., description="Content ID")
    new_ttl_seconds: int = Field(..., ge=60, le=86400, description="New TTL in seconds (60-86400)")


class PopularityForecast(BaseModel):
    """Popularity forecast for content"""
    content_id: str = Field(..., description="Content ID")
    predicted_requests_next_window: int = Field(..., ge=0, description="Predicted requests in next time window")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")


class AIDecisionResponse(BaseModel):
    """Complete AI decision response"""
    popularity_forecast: List[Dict[str, Any]] = Field(..., description="Popularity predictions")
    prefetch_plan: List[Dict[str, Any]] = Field(default_factory=list, description="Prefetch decisions")
    eviction_plan: List[Dict[str, Any]] = Field(default_factory=list, description="Eviction decisions")
    ttl_updates: List[Dict[str, Any]] = Field(default_factory=list, description="TTL update decisions")
    decision_timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Decision timestamp"
    )
    model_mode: str = Field(..., description="Model mode used (local/rules/api)")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


class DecisionRequest(BaseModel):
    """Request for AI decisions"""
    request_logs: List[dict] = Field(..., description="Recent request logs")
    content_metadata: List[dict] = Field(..., description="Content metadata")
    edge_constraints: List[dict] = Field(..., description="Edge cache constraints")
    trend_signals: Optional[List[dict]] = Field(None, description="Optional trend signals")
    time_window_minutes: int = Field(60, ge=1, le=1440, description="Prediction time window in minutes")
