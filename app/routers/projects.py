from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Project, StreetPhoto, PerceptionPrediction, User
from app.routers.auth import get_current_user
from app.routers.street_photos import execute_full_cascade_delete_photo
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectResponseWithStats, PaginatedProjectResponse, VisualQualityReportResponse, VisualIndicatorItem, ProjectUviSummary, ModelReferenceSection, ObservationSection
from app.schemas.home_dashboard import HomeDashboardResponse

# pagination
from math import ceil
from typing import List, Optional

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

    UPLOAD_DIR = "uploads/photos"
    latest_photo = (
        db.query(StreetPhoto.file_path)
        .filter(
            StreetPhoto.project_id == project_id,
            StreetPhoto.file_path.ilike(f"{UPLOAD_DIR}/%")  # Memastikan hanya mengambil folder foto
        )
        .order_by(StreetPhoto.created_at.desc())  # Ambil yang paling baru
        .first()
    )
    project_avatar = latest_photo[0] if latest_photo else None

    return {
        "photo_count": photo_count,
        "video_count": video_count,
        "beauty_score": float(scores[0]) if scores and scores[0] is not None else None,
        "safety_score": float(scores[1]) if scores and scores[1] is not None else None,
        "comfort_score": float(scores[2]) if scores and scores[2] is not None else None,
        "uvi_score": float(scores[3]) if scores and scores[3] is not None else None,
        "project_avatar": project_avatar
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
@router.get("/", response_model=PaginatedProjectResponse)
def list_projects(
    page: int = Query(1, ge=1, description="Nomor halaman yang ingin diakses"),
    size: int = Query(10, ge=1, le=100, description="Jumlah data maksimal per halaman"),
    search: Optional[str] = Query(None, description="Cari project berdasarkan nama"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"

    # Lakukan explicit join ke tabel User berdasarkan Project.created_by
    base_query = db.query(Project, User).outerjoin(
        User, Project.created_by == User.id
    )

    if not is_admin:
        base_query = base_query.filter(Project.created_by == current_user.id)

    if search:
        base_query = base_query.filter(Project.name.ilike(f"%{search}%"))

    total_data = base_query.count()
    total_pages = ceil(total_data / size) if total_data > 0 else 1
    skip = (page - 1) * size

    # Hasil query sekarang berupa list of tuple: (Project, User)
    results = (
        base_query
        .order_by(sa_func.coalesce(Project.last_opened_at, Project.created_at).desc())
        .offset(skip)
        .limit(size)
        .all()
    )

    result_data = []
    # Looping tuple hasil join
    for project, creator in results:
        stats = _compute_project_stats(project.id, db)
        
        # Siapkan dictionary untuk data creator jika ada
        creator_data = None
        if creator:
            creator_data = {
                "id": creator.id,
                "name": creator.name,
                "email": creator.email,
                "profile_file_path": getattr(creator, "profile_file_path", None)
            }

        result_data.append(ProjectResponseWithStats(
            **ProjectResponse.model_validate(project).model_dump(),
            **stats,
            creator=creator_data # Sisipkan data creator ke response
        ))

    return {
        "total_data": total_data,
        "total_pages": total_pages,
        "current_page": page,
        "data": result_data
    }

# 2.5. GET TOTAL PROJECT COUNT (Khusus Dashboard Widget)
# @router.get("/count", response_model=dict)
# def get_total_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     total_count = db.query(Project).count()
#     return {
#         "status": "success",
#         "total_projects": total_count
#     }
@router.get("/count", response_model=dict)
def get_total_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Cek apakah user adalah admin
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"

    query = db.query(Project)

    # Batasi hitungan hanya untuk project yang dibuat oleh user tersebut jika bukan admin
    if not is_admin:
        query = query.filter(Project.created_by == current_user.id)

    total_count = query.count()
    
    return {
        "status": "success",
        "total_projects": total_count
    }

@router.get("/home-dashboard", response_model=HomeDashboardResponse)
def get_home_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Cek apakah user adalah admin (sesuaikan pengecekan role/is_admin dengan model User kamu)
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"

    # 1. Hitung total project (berdasarkan pembuat jika bukan admin)
    project_query = db.query(Project)
    if not is_admin:
        project_query = project_query.filter(Project.created_by == current_user.id)
    total_projects = project_query.count()

    # 2. Hitung rata-rata skor persepsi dengan join berjenjang ke StreetPhoto dan Project
    avg_query = db.query(
        sa_func.avg(PerceptionPrediction.safety_score),
        sa_func.avg(PerceptionPrediction.beauty_score),
        sa_func.avg(PerceptionPrediction.comfort_score),
        sa_func.avg(PerceptionPrediction.uvi_score),
    ).join(
        StreetPhoto, PerceptionPrediction.photo_id == StreetPhoto.id
    ).join(
        Project, StreetPhoto.project_id == Project.id
    )

    # Filter berdasarkan pembuat project jika bukan admin
    if not is_admin:
        avg_query = avg_query.filter(Project.created_by == current_user.id)

    avg_scores = avg_query.first()

    # 3. Amankan nilai jika hasilnya None (misal tabel kosong atau user belum punya data upload sama sekali -> otomatis 0.0)
    safety = float(avg_scores[0]) if avg_scores and avg_scores[0] is not None else 0.0
    beauty = float(avg_scores[1]) if avg_scores and avg_scores[1] is not None else 0.0
    comfort = float(avg_scores[2]) if avg_scores and avg_scores[2] is not None else 0.0
    uvi = float(avg_scores[3]) if avg_scores and avg_scores[3] is not None else 0.0

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

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import PerceptionPrediction, Project, SegmentationResult, StreetPhoto, User
from app.routers.auth import get_current_user


def _normalize_pct(value: Optional[float], is_ratio: bool = False) -> float:
    """
    Amankan None -> 0.0 dan konversi skala 0.0-1.0 ke persen (0-100) jika kolom bertipe rasio.
    """
    if value is None:
        return 0.0
    val = float(value)
    if is_ratio and val <= 1.0:
        val = val * 100.0
    return round(val, 1)


@router.get("/visual-quality-report", response_model=VisualQualityReportResponse)
def get_visual_quality_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"

    # 1. TOTAL PROJECT (Filter role)
    project_query = db.query(Project)
    if not is_admin:
        project_query = project_query.filter(Project.created_by == current_user.id)
    total_projects = project_query.count()

    # 2. UVI RATA-RATA & CAKUPAN ANALISIS (Persentase bulat dari UVI rata-rata)
    uvi_query = (
        db.query(sa_func.avg(PerceptionPrediction.uvi_score))
        .join(StreetPhoto, PerceptionPrediction.photo_id == StreetPhoto.id)
        .join(Project, StreetPhoto.project_id == Project.id)
    )
    if not is_admin:
        uvi_query = uvi_query.filter(Project.created_by == current_user.id)

    raw_avg_uvi = uvi_query.scalar()
    average_uvi = round(float(raw_avg_uvi), 2) if raw_avg_uvi is not None else 0.0
    # Jika skala UVI 0.0 - 1.0 -> kalikan 100 jadi persentase bulat
    analysis_coverage_pct = round(average_uvi * 100) if average_uvi <= 1.0 else round(average_uvi)

    # 3. INDIKATOR LINGKUNGAN VISUAL (Tahap 1: Rata-rata per variabel secara terpisah)
    seg_query = (
        db.query(
            sa_func.avg(SegmentationResult.building_pct),
            sa_func.avg(SegmentationResult.vegetation_pct),
            sa_func.avg(SegmentationResult.sky_pct),
            sa_func.avg(SegmentationResult.walkability_ratio),
            sa_func.avg(SegmentationResult.visual_clutter_index),
        )
        .join(StreetPhoto, SegmentationResult.photo_id == StreetPhoto.id)
        .join(Project, StreetPhoto.project_id == Project.id)
    )
    if not is_admin:
        seg_query = seg_query.filter(Project.created_by == current_user.id)

    seg_avgs = seg_query.first()

    indicators: list[VisualIndicatorItem] = [
        VisualIndicatorItem(
            key="building_visibility_index",
            label="Indeks Keterlihatan Bangunan",
            value=_normalize_pct(seg_avgs[0] if seg_avgs else None, is_ratio=False),
        ),
        VisualIndicatorItem(
            key="vegetation_coverage_index",
            label="Indeks Cakupan Vegetasi",
            value=_normalize_pct(seg_avgs[1] if seg_avgs else None, is_ratio=False),
        ),
        VisualIndicatorItem(
            key="sky_openness_index",
            label="Indeks Keterbukaan Langit",
            value=_normalize_pct(seg_avgs[2] if seg_avgs else None, is_ratio=False),
        ),
        VisualIndicatorItem(
            key="surface_accessibility_index",
            label="Indeks Aksesibilitas Permukaan",
            value=_normalize_pct(seg_avgs[3] if seg_avgs else None, is_ratio=True),
        ),
        VisualIndicatorItem(
            key="visual_dominance_index",
            label="Indeks Dominasi Visual",
            value=_normalize_pct(seg_avgs[4] if seg_avgs else None, is_ratio=True),
        ),
    ]

    # Tahap 2: Bandingkan ke-5 rata-rata variabel untuk mencari skor tertinggi & terendah
    has_indicator_data = any(item.value > 0 for item in indicators)
    if has_indicator_data:
        sorted_indicators = sorted(indicators, key=lambda x: x.value, reverse=True)
        highest_indicator = sorted_indicators[0]
        lowest_indicator = sorted_indicators[-1]
    else:
        highest_indicator = VisualIndicatorItem(key="-", label="-", value=0.0)
        lowest_indicator = VisualIndicatorItem(key="-", label="-", value=0.0)

    # 4. OBSERVASI PERBANDINGAN UVI ANTAR PROJECT (Tertinggi vs Terendah)
    project_uvi_query = (
        db.query(
            Project.id,
            Project.name,
            sa_func.avg(PerceptionPrediction.uvi_score).label("avg_uvi"),
        )
        .join(StreetPhoto, StreetPhoto.project_id == Project.id)
        .join(PerceptionPrediction, PerceptionPrediction.photo_id == StreetPhoto.id)
        .filter(PerceptionPrediction.uvi_score.isnot(None))
    )
    if not is_admin:
        project_uvi_query = project_uvi_query.filter(Project.created_by == current_user.id)

    project_rankings = (
        project_uvi_query
        .group_by(Project.id, Project.name)
        .order_by(sa_func.avg(PerceptionPrediction.uvi_score).desc())
        .all()
    )

    observation_bullets: list[str] = []

    if len(project_rankings) >= 2:
        top_proj = project_rankings[0]
        low_proj = project_rankings[-1]
        highest_project = ProjectUviSummary(
            project_id=top_proj.id,
            project_name=top_proj.name,
            uvi_score=round(float(top_proj.avg_uvi), 2),
        )
        lowest_project = ProjectUviSummary(
            project_id=low_proj.id,
            project_name=low_proj.name,
            uvi_score=round(float(low_proj.avg_uvi), 2),
        )
        observation_bullets.append(
            f"{highest_project.project_name} memiliki UVI {highest_project.uvi_score:.2f}, "
            f"dibandingkan dengan {lowest_project.uvi_score:.2f} untuk {lowest_project.project_name}."
        )
    elif len(project_rankings) == 1:
        only_proj = project_rankings[0]
        highest_project = ProjectUviSummary(
            project_id=only_proj.id,
            project_name=only_proj.name,
            uvi_score=round(float(only_proj.avg_uvi), 2),
        )
        lowest_project = ProjectUviSummary(project_id=None, project_name="-", uvi_score=0.0)
        observation_bullets.append(
            f"{highest_project.project_name} memiliki UVI {highest_project.uvi_score:.2f} "
            f"(diperlukan minimal 2 proyek teranalisis untuk perbandingan skor tertinggi dan terendah)."
        )
    else:
        highest_project = ProjectUviSummary(project_id=None, project_name="-", uvi_score=0.0)
        lowest_project = ProjectUviSummary(project_id=None, project_name="-", uvi_score=0.0)
        observation_bullets.append(
            "Belum ada data proyek dengan hasil prediksi UVI yang dapat dibandingkan."
        )

    if has_indicator_data:
        top_two = sorted(indicators, key=lambda x: x.value, reverse=True)[:2]
        observation_bullets.append(
            f"Penjelasan parameter menunjukkan kontribusi positif "
            f"{top_two[0].label.replace('Indeks ', '').lower()} ({top_two[0].value}%) dan "
            f"{top_two[1].label.replace('Indeks ', '').lower()} ({top_two[1].value}%)."
        )
    else:
        observation_bullets.append(
            "Indikator lingkungan visual belum tersedia karena belum ada foto yang selesai disegmentasi."
        )

    observation_bullets.append(
        "Cakupan foto tambahan dan pengambilan sampel yang konsisten diperlukan sebelum menyimpulkan kondisi seluruh koridor."
    )

    # 5. HARDCODE REFERENSI MODEL DAN PREDIKSI (Sesuai spesifikasi UI)
    model_reference = ModelReferenceSection(
        uvi_reference=0.82,
        prediction_confidence_pct=91,
        task_title="Segmentasi Semantik",
        task_subtitle="Informasi model",
        model_name="SegFormer-B5",
        architecture="encoder MiT-B5 + decoder all-MLP",
        publication="NeurIPS 2021",
        miou_reference_pct=84.0,
        inference_time_sec=0.42,
    )

    return VisualQualityReportResponse(
        status="success",
        total_projects=total_projects,
        average_uvi=average_uvi,
        analysis_coverage_pct=analysis_coverage_pct,
        # summary_text="Laporan ini menggabungkan foto jalan, indikator komposisi visual, dan skor UVI untuk tinjauan proyek.",
        observations=ObservationSection(
            highest_project=highest_project,
            lowest_project=lowest_project,
            # highest_indicator=highest_indicator,
            # lowest_indicator=lowest_indicator,
            # bullets=observation_bullets,
        ),
        model_reference=model_reference,
        visual_environment_indicators=indicators,
        # next_steps_text=(
        #     "Review image quality, validate segmentation against human annotations, "
        #     "and define the UVI scoring method before using scores for decisions. "
        #     "Tinjau lokasi berskor rendah sesuai konteks setempat."
        # ),
    )


# 3. GET BY ID (dengan stats)
@router.get("/{project_id}", response_model=ProjectResponseWithStats)
def get_project(
    project_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Cek hak akses admin
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "admin"

    # 1. Query Project sekaligus join ke tabel User (creator)
    result = (
        db.query(Project, User)
        .outerjoin(User, Project.created_by == User.id)
        .filter(Project.id == project_id)
        .first()
    )

    # 2. Jika project tidak ditemukan di database
    if not result:
        raise HTTPException(status_code=404, detail="Project tidak ditemukan")
    
    project, creator = result

    # 3. Validasi Hak Akses Kepemilikan (Penting!)
    # Jika bukan admin DAN bukan pembuat project tersebut, tolak aksesnya
    if not is_admin and project.created_by != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Anda tidak memiliki izin untuk mengakses project ini"
        )

    # 4. Update waktu terakhir dibuka
    project.last_opened_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)

    # 5. Hitung statistik project
    stats = _compute_project_stats(project.id, db)

    # 6. Siapkan dictionary data creator
    creator_data = None
    if creator:
        creator_data = {
            "id": creator.id,
            "name": creator.name,
            "email": creator.email,
            "profile_file_path": getattr(creator, "profile_file_path", None)
        }

    # 7. Gabungkan semua dan kembalikan response
    return ProjectResponseWithStats(
        **ProjectResponse.model_validate(project).model_dump(),
        **stats,
        creator=creator_data
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