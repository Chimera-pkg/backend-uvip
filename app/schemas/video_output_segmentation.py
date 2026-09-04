from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.db.enums import ModelType

class VideoOutputSegmentationCreate(BaseModel):
    photo_id: UUID
    video_url: Optional[str] = None
    fps: Optional[float] = None
    frame_count: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    duration_seconds: Optional[float] = None
    frames_processed: Optional[float] = None
    processing_time_ms: Optional[float] = None

class VideoOutputSegmentationUpdate(BaseModel):
    photo_id: UUID
    video_url: Optional[str] = None
    fps: Optional[float] = None
    frame_count: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    duration_seconds: Optional[float] = None
    frames_processed: Optional[float] = None
    processing_time_ms: Optional[float] = None

class VideoOutputSegmentationResponse(BaseModel):
    id: UUID
    photo_id: UUID
    video_url: Optional[str] = None
    fps: Optional[float] = None
    frame_count: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    duration_seconds: Optional[float] = None
    frames_processed: Optional[float] = None
    processing_time_ms: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

    # Validator untuk menambahkan URL AI
    @field_validator('video_url')
    @classmethod
    def prepend_ai_base_url(cls, v: Optional[str]) -> Optional[str]:
        # Jika nilainya ada, dan belum memiliki awalan 'http'
        if v and not v.startswith('http'):
            # Hapus '/' di awal string jika kebetulan ada, lalu gabung dengan IP AI
            clean_path = v.lstrip('/')
            return f"http://80.241.214.39:8002/{clean_path}"
        return v