from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import TargetIndicator

class ShapValueCreate(BaseModel):
    prediction_id: UUID
    target_indicator: TargetIndicator
    feature_name: str
    display_label: Optional[str] = None
    shap_value: float
    is_positive: Optional[bool] = None
    rank_order: Optional[int] = None

class ShapValueUpdate(BaseModel):
    prediction_id: Optional[UUID] = None
    target_indicator: Optional[TargetIndicator] = None
    feature_name: Optional[str] = None
    display_label: Optional[str] = None
    shap_value: Optional[float] = None
    is_positive: Optional[bool] = None
    rank_order: Optional[int] = None

class ShapValueResponse(BaseModel):
    id: UUID
    prediction_id: UUID
    target_indicator: TargetIndicator
    feature_name: str
    display_label: Optional[str]
    shap_value: float
    is_positive: Optional[bool]
    rank_order: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True