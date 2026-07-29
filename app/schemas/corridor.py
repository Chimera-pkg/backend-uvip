from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class CorridorCreate(BaseModel):
    name: str
    city: Optional[str] = "MALANG"
    district: Optional[str] = None
    length_km: Optional[float] = None
    description: Optional[str] = None
    geom: Optional[str] = None

class CorridorUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    length_km: Optional[float] = None
    description: Optional[str] = None

class CorridorResponse(BaseModel):
    id: UUID
    name: str
    city: Optional[str]
    district: Optional[str]
    length_km: Optional[float]
    description: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True