from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MissionAssignmentCreate(BaseModel):
    mission_id: UUID
    user_id: UUID

class MissionAssignmentUpdate(BaseModel):
    mission_id: UUID
    user_id: UUID

class MissionAssignmentResponse(BaseModel):
    id: UUID
    mission_id: UUID
    user_id: UUID
    assigned_at: datetime

    class Config:
        from_attributes = True