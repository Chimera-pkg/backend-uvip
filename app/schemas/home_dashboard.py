from pydantic import BaseModel
from typing import Optional

class HomeDashboardResponse(BaseModel):
    status: str
    total_projects: int
    average_scores: dict[str, Optional[float]]