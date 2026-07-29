from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import BatchJobStatus

class BatchUploadJobCreate(BaseModel):
    mission_id: Optional[UUID] = None
    zip_filename: Optional[str] = None
    zip_file_path: Optional[str] = None
    total_photos: Optional[int] = 0
    processed_photos: Optional[int] = 0
    failed_photos: Optional[int] = 0
    status: Optional[BatchJobStatus] = BatchJobStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_log: Optional[str] = None

class BatchUploadJobUpdate(BaseModel):
    mission_id: Optional[UUID] = None
    zip_filename: Optional[str] = None
    zip_file_path: Optional[str] = None
    total_photos: Optional[int] = None
    processed_photos: Optional[int] = None
    failed_photos: Optional[int] = None
    status: Optional[BatchJobStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_log: Optional[str] = None

class BatchUploadJobResponse(BaseModel):
    id: UUID
    created_by: Optional[UUID]
    mission_id: Optional[UUID]
    zip_filename: Optional[str]
    zip_file_path: Optional[str]
    total_photos: int
    processed_photos: int
    failed_photos: int
    status: BatchJobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_log: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True