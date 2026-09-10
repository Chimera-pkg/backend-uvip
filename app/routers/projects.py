from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Project, StreetPhoto, PerceptionPrediction, User
from app.routers.auth import get_current_user
from app.routers.street_photos import execute_full_cascade_delete_photo
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectResponseWithStats
from app.schemas.home_dashboard import HomeDashboardResponse

router = APIRouter(prefix="/projects", tags=["Projects"])

PHOTO_DIR_PREFIX = "uploads/photos/%"
VIDEO_DIR_PREFIX = "uploads/videos/%"


def _get_project_or_404(project_id: UUID, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")
    return project


def _compute_project_stats(project_id: UUID, db: Session) -> dict:
    """Agregat jumlah media + rata-rata skor persepsi dari semua foto/video project."""
    media_query = db.query(StreetPhoto).filter(StreetPhoto.project_id == project_id)
    photo_count = media_query.filter(
        StreetPhoto.file_path.ilike(PHOTO_DIR_PREFIX)
    ).count()
    video_count = media_query.filter(
        StreetPhoto.file_path.ilike(VIDEO_DIR_PREFIX)
    ).count()

    scores = (
        db.query(
            sa_func.avg(PerceptionPrediction.beauty_score),
            sa_func.avg(PerceptionPrediction.safety_score),
            sa_func.avg(PerceptionPrediction.comfort_score),
            sa_func.avg(PerceptionPrediction.uvi_score),
        )
        .join(StreetPhoto, StreetPhoto.id == PerceptionPrediction.photo_id)
        .filter(StreetPhoto.project_id == project_id)
        .first()
    )

    return {
        "photo_count": photo_count,
        "video_count": video_count,
        "beauty_score": float(scores[0]) if scores and scores[0] is not None else None,
        "safety_score": float(scores[1]) if scores and scores[1] is not None else None,
        "comfort_score": float(scores[2]) if scores and scores[2] is not None else None,
        "uvi_score": float(scores[3]) if scores and scores[3] is not None else None,
    }


# 1. CREATE
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_project = db.query(Project).filter(Project.name == data.name).first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project dengan nama '{data.name}' sudah ada. Gunakan nama lain."
        )

    project = Project(**data.model_dump(), created_by=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


# 2. LIST ALL (dengan stats: jumlah media + rata-rata skor)
@router.get("/", response_model=list[ProjectResponseWithStats])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = (
        db.query(Project)
        .order_by(sa_func.coalesce(Project.last_opened_at, Project.created_at).desc())
        .all()
    )
    result = []
    for project in projects:
        stats = _compute_project_stats(project.id, db)
        result.append(ProjectResponseWithStats(
            **ProjectResponse.model_validate(project).model_dump(),
            **stats,
        ))
    return result

# 2.5. GET TOTAL PROJECT COUNT (Khusus Dashboard Widget)
@router.get("/count", response_model=dict)
def get_total_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_count = db.query(Project).count()
    return {
        "status": "success",
        "total_projects": total_count
    }

@router.get("/home-dashboard", response_model=HomeDashboardResponse)
def get_home_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Hitung total seluruh project
    total_projects = db.query(Project).count()

    # 2. Hitung rata-rata skor persepsi secara global
    avg_scores = (
        db.query(
            sa_func.avg(PerceptionPrediction.safety_score),
            sa_func.avg(PerceptionPrediction.beauty_score),
            sa_func.avg(PerceptionPrediction.comfort_score),
            sa_func.avg(PerceptionPrediction.uvi_score),
        )
        .first()
    )

    # 3. Amankan nilai jika hasilnya None (misal tabel masih kosong)
    safety = float(avg_scores[0]) if avg_scores and avg_scores[0] is not None else 0.0
    beauty = float(avg_scores[1]) if avg_scores and avg_scores[1] is not None else 0.0
    comfort = float(avg_scores[2]) if avg_scores and avg_scores[2] is not None else 0.0
    uvi = float(avg_scores[3]) if avg_scores and avg_scores[3] is not None else 0.0

    # Pastikan mengembalikan dictionary yang sesuai persis dengan struktur HomeDashboardResponse
    return {
        "status": "success",
        "total_projects": total_projects,
        "average_scores": {
            "safety_score": round(safety, 2),
            "beauty_score": round(beauty, 2),
            "comfort_score": round(comfort, 2),
            "uvi_score": round(uvi, 2),
        }
    }


# 3. GET BY ID (dengan stats)
@router.get("/{project_id}", response_model=ProjectResponseWithStats)
def get_project(project_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project_or_404(project_id, db)
    stats = _compute_project_stats(project.id, db)

    project.last_opened_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return ProjectResponseWithStats(
        **ProjectResponse.model_validate(project).model_dump(),
        **stats,
    )

# 4. UPDATE
@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: UUID, data: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project_or_404(project_id, db)
    update_data = data.model_dump(exclude_unset=True)
    
    if "name" in update_data and update_data["name"] != project.name:
        existing_project = db.query(Project).filter(
            Project.name == update_data["name"],
            Project.id != project_id
        ).first()
        
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project dengan nama '{update_data['name']}' sudah digunakan oleh project lain."
            )

    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(project, key, val)
    db.commit()
    db.refresh(project)
    return project


# 5. OPEN PROJECT (update last_opened_at)
# @router.put("/{project_id}/open", response_model=ProjectResponse)
# def open_project(project_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     project = _get_project_or_404(project_id, db)
#     project.last_opened_at = datetime.now(timezone.utc)
#     db.commit()
#     db.refresh(project)
#     return project


# 6. DELETE (cascade: hapus semua foto/video + file fisik + riwayat analisisnya)
@router.delete("/{project_id}")
def delete_project(project_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = _get_project_or_404(project_id, db)

    media_ids = [
        row.id for row in db.query(StreetPhoto.id)
        .filter(StreetPhoto.project_id == project_id).all()
    ]
    for media_id in media_ids:
        execute_full_cascade_delete_photo(photo_id=media_id, db=db)

    db.delete(project)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": f"Project '{project.name}' beserta {len(media_ids)} media dan seluruh riwayat analisisnya berhasil dihapus",
            "deleted_id": str(project_id),
            "deleted_media_count": len(media_ids),
        },
    )
