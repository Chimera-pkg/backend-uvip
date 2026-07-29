from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SegmentationResultCreate(BaseModel):
    photo_id: UUID
    model_name: Optional[str] = "SEGFORMER-B5"
    vegetation_pct: Optional[float] = None
    building_pct: Optional[float] = None
    road_pct: Optional[float] = None
    sidewalk_pct: Optional[float] = None
    sky_pct: Optional[float] = None
    signage_pct: Optional[float] = None
    vehicle_pct: Optional[float] = None
    pedestrian_pct: Optional[float] = None
    street_furniture_pct: Optional[float] = None
    green_coverage_pct: Optional[float] = None
    building_coverage_pct: Optional[float] = None
    sky_visibility_pct: Optional[float] = None
    walkability_ratio: Optional[float] = None
    visual_clutter_index: Optional[float] = None
    mask_file_path: Optional[str] = None
    inference_time_ms: Optional[int] = None

class SegmentationResultUpdate(BaseModel):
    photo_id: Optional[UUID] = None
    model_name: Optional[str] = None
    vegetation_pct: Optional[float] = None
    building_pct: Optional[float] = None
    road_pct: Optional[float] = None
    sidewalk_pct: Optional[float] = None
    sky_pct: Optional[float] = None
    signage_pct: Optional[float] = None
    vehicle_pct: Optional[float] = None
    pedestrian_pct: Optional[float] = None
    street_furniture_pct: Optional[float] = None
    green_coverage_pct: Optional[float] = None
    building_coverage_pct: Optional[float] = None
    sky_visibility_pct: Optional[float] = None
    walkability_ratio: Optional[float] = None
    visual_clutter_index: Optional[float] = None
    mask_file_path: Optional[str] = None
    inference_time_ms: Optional[int] = None

class SegmentationResultResponse(BaseModel):
    id: UUID
    photo_id: UUID
    model_name: str
    vegetation_pct: Optional[float]
    building_pct: Optional[float]
    road_pct: Optional[float]
    sidewalk_pct: Optional[float]
    sky_pct: Optional[float]
    signage_pct: Optional[float]
    vehicle_pct: Optional[float]
    pedestrian_pct: Optional[float]
    street_furniture_pct: Optional[float]
    green_coverage_pct: Optional[float]
    building_coverage_pct: Optional[float]
    sky_visibility_pct: Optional[float]
    walkability_ratio: Optional[float]
    visual_clutter_index: Optional[float]
    mask_file_path: Optional[str]
    inference_time_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True