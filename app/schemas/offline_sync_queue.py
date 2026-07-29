from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import SyncStatus

class OfflineSyncQueueCreate(BaseModel):
    device_id: str
    mission_id: Optional[UUID] = None
    local_file_path: Optional[str] = None
    latitude: float
    longitude: float
    gps_accuracy_m: Optional[float] = None
    compass_azimuth: Optional[float] = None
    is_manual_capture: Optional[bool] = False
    captured_at: datetime
    sync_status: Optional[SyncStatus] = SyncStatus.PENDING
    retry_count: Optional[int] = 0
    last_retry_at: Optional[datetime] = None
    synced_photo_id: Optional[UUID] = None
    error_message: Optional[str] = None
    synced_at: Optional[datetime] = None

class OfflineSyncQueueUpdate(BaseModel):
    device_id: Optional[str] = None
    mission_id: Optional[UUID] = None
    local_file_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    compass_azimuth: Optional[float] = None
    is_manual_capture: Optional[bool] = None
    captured_at: Optional[datetime] = None
    sync_status: Optional[SyncStatus] = None
    retry_count: Optional[int] = None
    last_retry_at: Optional[datetime] = None
    synced_photo_id: Optional[UUID] = None
    error_message: Optional[str] = None
    synced_at: Optional[datetime] = None

class OfflineSyncQueueResponse(BaseModel):
    id: UUID
    device_id: str
    user_id: Optional[UUID]
    mission_id: Optional[UUID]
    local_file_path: Optional[str]
    latitude: float
    longitude: float
    gps_accuracy_m: Optional[float]
    compass_azimuth: Optional[float]
    is_manual_capture: bool
    captured_at: datetime
    sync_status: SyncStatus
    retry_count: int
    last_retry_at: Optional[datetime]
    synced_photo_id: Optional[UUID]
    error_message: Optional[str]
    synced_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True