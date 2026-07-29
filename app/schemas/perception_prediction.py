from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class PerceptionPredictionCreate(BaseModel):
    photo_id: UUID
    segmentation_id: Optional[UUID] = None
    model_version: Optional[str] = None
    beauty_score: Optional[float] = None
    safety_score: Optional[float] = None
    comfort_score: Optional[float] = None
    uvi_score: Optional[float] = None
    gvi_score: Optional[float] = None
    inference_time_ms: Optional[int] = None
    r2_reference: Optional[float] = None

class PerceptionPredictionUpdate(BaseModel):
    photo_id: Optional[UUID] = None
    segmentation_id: Optional[UUID] = None
    model_version: Optional[str] = None
    beauty_score: Optional[float] = None
    safety_score: Optional[float] = None
    comfort_score: Optional[float] = None
    uvi_score: Optional[float] = None
    gvi_score: Optional[float] = None
    inference_time_ms: Optional[int] = None
    r2_reference: Optional[float] = None

class PerceptionPredictionResponse(BaseModel):
    id: UUID
    photo_id: UUID
    segmentation_id: Optional[UUID]
    model_version: Optional[str]
    beauty_score: Optional[float]
    safety_score: Optional[float]
    comfort_score: Optional[float]
    uvi_score: Optional[float]
    gvi_score: Optional[float]
    inference_time_ms: Optional[int]
    r2_reference: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True