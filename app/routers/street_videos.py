import os
import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from geoalchemy2 import WKTElement

from app.db.database import get_db
# from app.db.models import StreetPhoto, User, SegmentationResult
from app.db.models import (
    StreetPhoto,
    SegmentationResult,
    PerceptionPrediction,
    ShapValue,
    SimulationSession,
    SimulationResult,
    PolicyRecommendation,
    OfflineSyncQueue,
    User
)
from app.db.enums import PhotoSource, ProcessingStatus
from app.routers.auth import get_current_user
from app.routers.segmentation_results import create_segmentation
from app.routers.street_photos import execute_full_cascade_delete_photo
from app.schemas.segmentation_result import SegmentationResultCreate
from app.schemas.street_photo import StreetPhotoResponse, StreetPhotoUpdate, PaginatedStreetPhotoResponse

# pagination
from fastapi import Query
from math import ceil

router = APIRouter(prefix="/street-videos", tags=["Street Videos"])

# Folder khusus penyimpanan video di server
VIDEO_UPLOAD_DIR = "uploads/videos"
os.makedirs(VIDEO_UPLOAD_DIR, exist_ok=True)


# 1. CREATE (STREAMING UPLOAD VIDEO + SIMPAN METADATA)
@router.post("/", response_model=StreetPhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_street_video(
    # File Video dari Client
    file: UploadFile = File(..., description="File Video (.mp4, .mov, .avi, .mkv, .webm)"),
    
    # Metadata Form Input
    source: PhotoSource = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    captured_at: datetime = Form(...),
    mission_id: Optional[UUID] = Form(None),
    gps_accuracy_m: Optional[float] = Form(None),
    compass_azimuth: Optional[float] = Form(None),
    exif_timestamp: Optional[datetime] = Form(None),
    is_manual_capture: bool = Form(False),
    is_offline_sync: bool = Form(False),
    
    # Injeksi DB & User
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Validasi Ekstensi File Video
    allowed_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file video tidak didukung! Format yang diizinkan: {', '.join(allowed_extensions)}"
        )

    # 2. Generate nama file unik dengan UUID
    saved_filename = f"{uuid.uuid4()}{file_ext}"
    relative_file_path = os.path.join(VIDEO_UPLOAD_DIR, saved_filename).replace("\\", "/")

    # 3. Simpan file secara Chunk Streaming (Aman untuk RAM saat video ratusan MB/GB)
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB per chunk buffer

    try:
        with open(relative_file_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)
                total_bytes += len(chunk)
    except Exception as e:
        # Hapus file jika proses tulis gagal di tengah jalan
        if os.path.exists(relative_file_path):
            os.remove(relative_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengunggah file video: {str(e)}"
        )
    finally:
        await file.close()

    file_size_kb = int(total_bytes / 1024)

    # 4. Buat titik geometri PostGIS (POINT SRID 4326: Longitude Latitude)
    geom_point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

    # 5. Simpan Record ke Database
    video_record = StreetPhoto(
        mission_id=mission_id,
        uploaded_by=current_user.id,
        source=source,
        original_filename=file.filename,
        file_path=relative_file_path,
        file_size_kb=file_size_kb,
        latitude=latitude,
        longitude=longitude,
        geom=geom_point,
        gps_accuracy_m=gps_accuracy_m,
        compass_azimuth=compass_azimuth,
        exif_timestamp=exif_timestamp,
        is_manual_capture=is_manual_capture,
        is_offline_sync=is_offline_sync,
        captured_at=captured_at,
        processing_status=ProcessingStatus.QUEUED
    )

    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    # dummy segmentation start
    segmentation_data = SegmentationResultCreate(
        photo_id=video_record.id,
        model_name="SEGFORMER-B5",
        vegetation_pct=10,
        building_pct=20,
        road_pct=30,
        sidewalk_pct=40,
        sky_pct=50,
        signage_pct=60,
        vehicle_pct=70,
        pedestrian_pct=0,
        street_furniture_pct=0,
        green_coverage_pct=0,
        building_coverage_pct=0,
        sky_visibility_pct=0,
        walkability_ratio=0,
        visual_clutter_index=0,
        mask_file_path=relative_file_path,
        inference_time_ms=0
    )
    create_segmentation(data=segmentation_data, db=db, current_user=current_user)
    # dummy segmentation end
    return video_record


# 2. READ ALL VIDEOS (Filter khusus file path yang tersimpan di direktori video)
# @router.get("/", response_model=List[StreetPhotoResponse])
# def list_videos(
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(get_current_user)
# ):
#     return db.query(StreetPhoto).filter(
#         StreetPhoto.file_path.ilike(f"{VIDEO_UPLOAD_DIR}/%")
#     ).all()
@router.get("/", response_model=PaginatedStreetPhotoResponse)
def list_videos(
    page: int = Query(1, ge=1, description="Nomor halaman yang ingin diakses"),
    size: int = Query(10, ge=1, le=100, description="Jumlah data maksimal per halaman"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    base_query = db.query(StreetPhoto).filter(
        StreetPhoto.file_path.ilike(f"{VIDEO_UPLOAD_DIR}/%")
    )

    total_data = base_query.count()
    total_pages = ceil(total_data / size) if total_data > 0 else 1
    skip = (page - 1) * size
    photos = base_query.order_by(StreetPhoto.created_at.desc()).offset(skip).limit(size).all()

    return {
        "total_data": total_data,
        "total_pages": total_pages,
        "current_page": page,
        "data": photos
    }


# 3. READ BY ID
@router.get("/{video_id}", response_model=StreetPhotoResponse)
def get_video(
    video_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    video = db.query(StreetPhoto).filter(
        StreetPhoto.id == video_id,
        StreetPhoto.file_path.ilike(f"{VIDEO_UPLOAD_DIR}/%")
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="File video tidak ditemukan"
        )
    return video


# 4. UPDATE BY ID
@router.put("/{video_id}", response_model=StreetPhotoResponse)
def update_video(
    video_id: UUID, 
    data: StreetPhotoUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    video = db.query(StreetPhoto).filter(
        StreetPhoto.id == video_id,
        StreetPhoto.file_path.ilike(f"{VIDEO_UPLOAD_DIR}/%")
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="File video tidak ditemukan"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Update otomatis geom jika latitude/longitude diubah
    lat = update_data.get("latitude", video.latitude)
    lon = update_data.get("longitude", video.longitude)
    if "latitude" in update_data or "longitude" in update_data:
        update_data["geom"] = WKTElement(f"POINT({lon} {lat})", srid=4326)

    for key, val in update_data.items():
        setattr(video, key, val)

    db.commit()
    db.refresh(video)
    return video


# 5. DELETE BY ID (TERMASUK HAPUS FILE FISIK DARI STORAGE)
# @router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_video(
#     video_id: UUID, 
#     db: Session = Depends(get_db), 
#     current_user: User = Depends(get_current_user)
# ):
#     video = db.query(StreetPhoto).filter(
#         StreetPhoto.id == video_id,
#         StreetPhoto.file_path.ilike(f"{VIDEO_UPLOAD_DIR}/%")
#     ).first()
    
#     if not video:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, 
#             detail="File video tidak ditemukan"
#         )
    
#     # Hapus file fisik dari server
#     if os.path.exists(video.file_path):
#         try:
#             os.remove(video.file_path)
#         except OSError:
#             pass

#     db.delete(video)
#     db.commit()
#     return JSONResponse(
#         status_code=status.HTTP_200_OK,
#         content={
#             "status": "success",
#             "message": "File video berhasil dihapus",
#             "deleted_id": str(video_id)
#         }
#     )

@router.delete("/{video_id}")
def delete_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # validasi benar file video
    video = db.query(StreetPhoto).filter(
        StreetPhoto.id == video_id,
        StreetPhoto.file_path.ilike("uploads/videos/%")
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File video tidak ditemukan"
        )

    execute_full_cascade_delete_photo(photo_id=video_id, db=db)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "File video beserta seluruh riwayat analisis & simulasinya berhasil dihapus bersih",
            "deleted_id": str(video_id)
        }
    )