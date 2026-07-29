from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SimulationSessionCreate(BaseModel):
    corridor_id: Optional[UUID] = None
    base_photo_id: Optional[UUID] = None
    base_prediction_id: Optional[UUID] = None
    vegetation_adjustment_pct: Optional[float] = 0
    sidewalk_width_adjustment_pct: Optional[float] = 0
    signage_density_adjustment_pct: Optional[float] = 0
    session_label: Optional[str] = None
    notes: Optional[str] = None

class SimulationSessionUpdate(BaseModel):
    corridor_id: Optional[UUID] = None
    base_photo_id: Optional[UUID] = None
    base_prediction_id: Optional[UUID] = None
    vegetation_adjustment_pct: Optional[float] = None
    sidewalk_width_adjustment_pct: Optional[float] = None
    signage_density_adjustment_pct: Optional[float] = None
    session_label: Optional[str] = None
    notes: Optional[str] = None

class SimulationSessionResponse(BaseModel):
    id: UUID
    created_by: UUID
    corridor_id: Optional[UUID]
    base_photo_id: Optional[UUID]
    base_prediction_id: Optional[UUID]
    vegetation_adjustment_pct: float
    sidewalk_width_adjustment_pct: float
    signage_density_adjustment_pct: float
    session_label: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True