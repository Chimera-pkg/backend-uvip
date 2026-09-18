# from typing import Optional
# from uuid import UUID
# from datetime import datetime
# from pydantic import BaseModel, Field


# class ProjectCreate(BaseModel):
#     name: str = Field(..., min_length=1, max_length=200)
#     location: Optional[str] = Field(None, max_length=200)
#     description: Optional[str] = None


# class ProjectUpdate(BaseModel):
#     name: Optional[str] = Field(None, min_length=1, max_length=200)
#     location: Optional[str] = Field(None, max_length=200)
#     description: Optional[str] = None


# class ProjectResponse(BaseModel):
#     id: UUID
#     name: str
#     location: Optional[str]
#     description: Optional[str]
#     created_by: UUID
#     last_opened_at: Optional[datetime]
#     created_at: datetime

#     class Config:
#         from_attributes = True


# class ProjectStats(BaseModel):
#     """Agregat skor persepsi project, dihitung dari perception_predictions
#     milik semua foto yang terhubung ke project."""
#     photo_count: int
#     video_count: int
#     beauty_score: Optional[float]
#     safety_score: Optional[float]
#     comfort_score: Optional[float]
#     uvi_score: Optional[float]


# class ProjectResponseWithStats(ProjectResponse):
#     photo_count: int = 0
#     video_count: int = 0
#     beauty_score: Optional[float] = None
#     safety_score: Optional[float] = None
#     comfort_score: Optional[float] = None
#     uvi_score: Optional[float] = None

# class PaginatedProjectResponse(BaseModel):
#     total_data: int
#     total_pages: int
#     current_page: int
#     data: List[ProjectResponseWithStats]

#     class Config:
#         from_attributes = True

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

# 3. Level Berikutnya: Response dengan Statistik (Turunan dari ProjectResponse)
class ProjectResponseWithStats(ProjectResponse):
    photo_count: int = 0
    video_count: int = 0
    beauty_score: Optional[float] = None
    safety_score: Optional[float] = None
    comfort_score: Optional[float] = None
    uvi_score: Optional[float] = None

# 4. Paling Bawah: Paginasi (Menggunakan ProjectResponseWithStats yang sudah pasti terbaca di atas)
class PaginatedProjectResponse(BaseModel):
    total_data: int
    total_pages: int
    current_page: int
    data: List[ProjectResponseWithStats]

    class Config:
        from_attributes = True