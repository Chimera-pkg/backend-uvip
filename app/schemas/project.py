from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

# 1. Paling Dasar: Base, Create, Update
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None

# 2. Level Berikutnya: Response Standar
class ProjectResponse(ProjectBase):
    id: UUID
    created_by: UUID
    last_opened_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectCreatorResponse(BaseModel):
    id: UUID
    name: str
    email: str
    profile_file_path: Optional[str] = None

    class Config:
        from_attributes = True

# 3. Level Berikutnya: Response dengan Statistik (Turunan dari ProjectResponse)
class ProjectResponseWithStats(ProjectResponse):
    photo_count: int = 0
    video_count: int = 0
    beauty_score: Optional[float] = None
    safety_score: Optional[float] = None
    comfort_score: Optional[float] = None
    uvi_score: Optional[float] = None
    project_avatar: Optional[str] = None
    creator: Optional[ProjectCreatorResponse] = None

# 4. Paginasi (Menggunakan ProjectResponseWithStats yang sudah pasti terbaca di atas)
class PaginatedProjectResponse(BaseModel):
    total_data: int
    total_pages: int
    current_page: int
    data: List[ProjectResponseWithStats]

    class Config:
        from_attributes = True

class ProjectUviSummary(BaseModel):
    project_id: Optional[UUID] = None
    project_name: str = "-"
    uvi_score: float = 0.0


class VisualIndicatorItem(BaseModel):
    key: str
    label: str
    value: float = 0.0  # dalam persen (0 - 100)


class ObservationSection(BaseModel):
    highest_project: ProjectUviSummary
    lowest_project: ProjectUviSummary
    # highest_indicator: VisualIndicatorItem
    # lowest_indicator: VisualIndicatorItem
    # bullets: List[str]


class ModelReferenceSection(BaseModel):
    uvi_reference: float
    prediction_confidence_pct: int
    task_title: str
    task_subtitle: str
    model_name: str
    architecture: str
    publication: str
    miou_reference_pct: float
    inference_time_sec: float


class VisualQualityReportResponse(BaseModel):
    status: str = "success"
    total_projects: int = 0
    average_uvi: float = 0.0
    analysis_coverage_pct: int = 0  # UVI rata-rata dalam persentase bulat
    # summary_text: str
    observations: ObservationSection
    model_reference: ModelReferenceSection
    visual_environment_indicators: List[VisualIndicatorItem]
    # next_steps_text: str