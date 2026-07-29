from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import ModelType

class ModelRegistryCreate(BaseModel):
    model_name: str
    model_type: ModelType
    version_tag: Optional[str] = None
    description: Optional[str] = None
    r2_score: Optional[float] = None
    mae_score: Optional[float] = None
    rmse_score: Optional[float] = None
    training_dataset: Optional[str] = None
    hardware_used: Optional[str] = None
    is_active: Optional[bool] = False
    trained_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None

class ModelRegistryUpdate(BaseModel):
    model_name: Optional[str] = None
    model_type: Optional[ModelType] = None
    version_tag: Optional[str] = None
    description: Optional[str] = None
    r2_score: Optional[float] = None
    mae_score: Optional[float] = None
    rmse_score: Optional[float] = None
    training_dataset: Optional[str] = None
    hardware_used: Optional[str] = None
    is_active: Optional[bool] = None
    trained_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None

class ModelRegistryResponse(BaseModel):
    id: UUID
    model_name: str
    model_type: ModelType
    version_tag: Optional[str]
    description: Optional[str]
    r2_score: Optional[float]
    mae_score: Optional[float]
    rmse_score: Optional[float]
    training_dataset: Optional[str]
    hardware_used: Optional[str]
    is_active: bool
    trained_at: Optional[datetime]
    deployed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True