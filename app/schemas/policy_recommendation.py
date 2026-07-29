from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import PolicyPriority

class PolicyRecommendationCreate(BaseModel):
    session_id: Optional[UUID] = None
    triggered_by: str
    threshold_score: Optional[float] = 5.00
    actual_score: Optional[float] = None
    recommendation_type: Optional[str] = None
    recommendation_text: str
    priority: Optional[PolicyPriority] = PolicyPriority.MEDIUM
    is_auto_generated: Optional[bool] = True

class PolicyRecommendationUpdate(BaseModel):
    session_id: Optional[UUID] = None
    triggered_by: Optional[str] = None
    threshold_score: Optional[float] = None
    actual_score: Optional[float] = None
    recommendation_type: Optional[str] = None
    recommendation_text: Optional[str] = None
    priority: Optional[PolicyPriority] = None
    is_auto_generated: Optional[bool] = None

class PolicyRecommendationResponse(BaseModel):
    id: UUID
    session_id: Optional[UUID]
    triggered_by: str
    threshold_score: Optional[float]
    actual_score: Optional[float]
    recommendation_type: Optional[str]
    recommendation_text: str
    priority: PolicyPriority
    is_auto_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True