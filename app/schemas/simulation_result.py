from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import SimulationIndicator

class SimulationResultCreate(BaseModel):
    session_id: UUID
    indicator: SimulationIndicator
    score_before: float
    score_after: float
    score_delta: Optional[float] = None
    inference_time_ms: Optional[int] = None

class SimulationResultUpdate(BaseModel):
    session_id: Optional[UUID] = None
    indicator: Optional[SimulationIndicator] = None
    score_before: Optional[float] = None
    score_after: Optional[float] = None
    score_delta: Optional[float] = None
    inference_time_ms: Optional[int] = None

class SimulationResultResponse(BaseModel):
    id: UUID
    session_id: UUID
    indicator: SimulationIndicator
    score_before: float
    score_after: float
    score_delta: Optional[float]
    inference_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True