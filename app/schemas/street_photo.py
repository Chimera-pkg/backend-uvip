from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.db.enums import PhotoSource, ProcessingStatus

class StreetPhotoCreate(BaseModel):
    mission_id: Optional[UUID] = None
    source: PhotoSource
    original_filename: Optional[str] = None
    file_path: str
    file_size_kb: Optional[int] = None
    latitude: float
    longitude: float
    gps_accuracy_m: Optional[float] = None
    compass_azimuth: Optional[float] = None
    exif_timestamp: Optional[datetime] = None
    is_manual_capture: Optional[bool] = False
    is_offline_sync: Optional[bool] = False
    privacy_masked: Optional[bool] = False
    processing_status: Optional[ProcessingStatus] = ProcessingStatus.QUEUED
    error_message: Optional[str] = None
    captured_at: datetime

class StreetPhotoUpdate(BaseModel):
    mission_id: Optional[UUID] = None
    source: Optional[PhotoSource] = None
    original_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size_kb: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_m: Optional[float] = None
    compass_azimuth: Optional[float] = None
    exif_timestamp: Optional[datetime] = None
    is_manual_capture: Optional[bool] = None
    is_offline_sync: Optional[bool] = None
    privacy_masked: Optional[bool] = None
    processing_status: Optional[ProcessingStatus] = None
    error_message: Optional[str] = None
    captured_at: Optional[datetime] = None

class StreetPhotoResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID]
    mission_id: Optional[UUID]
    uploaded_by: UUID
    source: PhotoSource
    original_filename: Optional[str]
    file_path: str
    file_size_kb: Optional[int]
    latitude: float
    longitude: float
    gps_accuracy_m: Optional[float]
    compass_azimuth: Optional[float]
    exif_timestamp: Optional[datetime]
    is_manual_capture: bool
    is_offline_sync: bool
    privacy_masked: bool
    processing_status: ProcessingStatus
    error_message: Optional[str]
    captured_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedStreetPhotoResponse(BaseModel):
    total_data: int
    total_pages: int
    current_page: int
    data: List[StreetPhotoResponse]
    
    class Config:
        from_attributes = True