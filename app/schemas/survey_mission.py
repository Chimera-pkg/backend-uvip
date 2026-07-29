from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import MissionStatus

class SurveyMissionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    corridor_id: Optional[UUID] = None
    status: Optional[MissionStatus] = MissionStatus.ACTIVE
    target_photo_count: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SurveyMissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    corridor_id: Optional[UUID] = None
    status: Optional[MissionStatus] = None
    target_photo_count: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SurveyMissionResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    corridor_id: Optional[UUID]
    created_by: UUID
    status: MissionStatus
    target_photo_count: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True