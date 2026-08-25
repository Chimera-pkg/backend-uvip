# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from typing import List
# from uuid import UUID

# from app.db.database import get_db
# from app.db.models import StreetPhoto, User
# from app.schemas.street_photo import StreetPhotoCreate, StreetPhotoResponse, StreetPhotoUpdate
# from app.routers.auth import get_current_user

# router = APIRouter(prefix="/street-photos", tags=["Street Photos"])

# @router.post("/", response_model=StreetPhotoResponse, status_code=status.HTTP_201_CREATED)
# def create_photo(data: StreetPhotoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     photo = StreetPhoto(**data.model_dump(), uploaded_by=current_user.id)
#     db.add(photo)
#     db.commit()
#     db.refresh(photo)
#     return photo

# @router.get("/", response_model=List[StreetPhotoResponse])
# def list_photos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return db.query(StreetPhoto).all()

# @router.get("/{photo_id}", response_model=StreetPhotoResponse)
# def get_photo(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
#     if not photo:
#         raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
#     return photo

# @router.put("/{photo_id}", response_model=StreetPhotoResponse)
# def update_photo(photo_id: UUID, data: StreetPhotoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
#     if not photo:
#         raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
#     for key, val in data.model_dump(exclude_unset=True).items():
#         setattr(photo, key, val)
#     db.commit()
#     db.refresh(photo)
#     return photo

# @router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_photo(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
#     if not photo:
#         raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
#     db.delete(photo)
#     db.commit()
#     return None

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
from app.schemas.street_photo import StreetPhotoResponse, StreetPhotoUpdate
from app.routers.auth import get_current_user

from app.routers.segmentation_results import create_segmentation
from app.schemas.segmentation_result import SegmentationResultCreate

router = APIRouter(prefix="/street-photos", tags=["Street Photos"])

# Folder tujuan penyimpanan foto di server
UPLOAD_DIR = "uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 1. CREATE (UPLOAD FOTO FISIK + SIMPAN METADATA)
@router.post("/", response_model=StreetPhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_street_photo(
    # File Fisik dari Client
    file: UploadFile = File(...),
    
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
    # Validation Format File
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Format file tidak didukung! Gunakan .jpg, .jpeg, .png, atau .webp"
        )

    # Buat nama file unik menggunakan UUID agar tidak menimpa file bernama sama
    saved_filename = f"{uuid.uuid4()}{file_ext}"
    relative_file_path = os.path.join(UPLOAD_DIR, saved_filename).replace("\\", "/")

    # Simpan file ke direktori server & hitung ukurannya
    try:
        contents = await file.read()
        file_size_kb = int(len(contents) / 1024)  # Hitung ukuran file dalam KB
        
        with open(relative_file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file: {str(e)}")

    # Buat titik geometri PostGIS (Point SRID 4326: Longitude dulu baru Latitude!)
    geom_point = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

    # Simpan record ke database
    photo = StreetPhoto(
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

    db.add(photo)
    db.commit()
    db.refresh(photo)

    # dummy segmentation start
    segmentation_data = SegmentationResultCreate(
        photo_id=photo.id,
        model_name="SEGFORMER-B5",
        vegetation_pct=0,
        building_pct=0,
        road_pct=0,
        sidewalk_pct=0,
        sky_pct=0,
        signage_pct=0,
        vehicle_pct=0,
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
    return photo


# 2. READ ALL
@router.get("/", response_model=List[StreetPhotoResponse])
def list_photos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(StreetPhoto).all()


# 3. READ BY ID
@router.get("/{photo_id}", response_model=StreetPhotoResponse)
def get_photo(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    return photo


# 4. UPDATE BY ID
@router.put("/{photo_id}", response_model=StreetPhotoResponse)
def update_photo(photo_id: UUID, data: StreetPhotoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Update otomatis geom jika latitude/longitude berubah
    lat = update_data.get("latitude", photo.latitude)
    long = update_data.get("longitude", photo.longitude)
    if "latitude" in update_data or "longitude" in update_data:
        update_data["geom"] = WKTElement(f"POINT({long} {lat})", srid=4326)

    for key, val in update_data.items():
        setattr(photo, key, val)

    db.commit()
    db.refresh(photo)
    return photo


# 5. DELETE BY ID (TERMASUK HAPUS FILE FISIK)
# @router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_photo(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
#     if not photo:
#         raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    
#     # Hapus file fisik dari server jika file-nya ada
#     if os.path.exists(photo.file_path):
#         os.remove(photo.file_path)

#     db.delete(photo)
#     db.commit()
#     return JSONResponse(
#         status_code=status.HTTP_200_OK,
#         content={
#             "status": "success",
#             "message": "File foto berhasil dihapus",
#             "deleted_id": str(photo_id)
#         }
#     )

@router.delete("/{photo_id}")
def delete_photo(
    photo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    execute_full_cascade_delete_photo(photo_id=photo_id, db=db)
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "File foto beserta seluruh riwayat analisis & simulasinya berhasil dihapus bersih",
            "deleted_id": str(photo_id)
        }
    )

def execute_full_cascade_delete_photo(photo_id: UUID, db: Session) -> None:
    """
    Menghapus record StreetPhoto beserta seluruh dependensi tabel anak
    secara berurutan dari level terdalam untuk menghindari ForeignKeyViolation.
    """
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foto/Video dengan ID '{photo_id}' tidak ditemukan."
        )

    db.query(OfflineSyncQueue).filter(
        OfflineSyncQueue.synced_photo_id == photo_id
    ).update({"synced_photo_id": None}, synchronize_session=False)

    predictions = db.query(PerceptionPrediction).filter(
        PerceptionPrediction.photo_id == photo_id
    ).all()
    prediction_ids = [p.id for p in predictions]

    sim_query = db.query(SimulationSession).filter(
        (SimulationSession.base_photo_id == photo_id) |
        (SimulationSession.base_prediction_id.in_(prediction_ids) if prediction_ids else False)
    )
    sim_sessions = sim_query.all()
    session_ids = [s.id for s in sim_sessions]

    # delete anak simulation_session
    if session_ids:
        # delete policy_recommendations
        db.query(PolicyRecommendation).filter(
            PolicyRecommendation.session_id.in_(session_ids)
        ).delete(synchronize_session=False)

        # delete simulation_results
        db.query(SimulationResult).filter(
            SimulationResult.session_id.in_(session_ids)
        ).delete(synchronize_session=False)

        # delete simulation_sessions
        db.query(SimulationSession).filter(
            SimulationSession.id.in_(session_ids)
        ).delete(synchronize_session=False)

    # delete perception_predictions
    if prediction_ids:
        db.query(ShapValue).filter(
            ShapValue.prediction_id.in_(prediction_ids)
        ).delete(synchronize_session=False)

        db.query(PerceptionPrediction).filter(
            PerceptionPrediction.id.in_(prediction_ids)
        ).delete(synchronize_session=False)

    # delete segmentation
    segmentation = db.query(SegmentationResult).filter(
        SegmentationResult.photo_id == photo_id
    ).first()

    if segmentation:
        if segmentation.mask_file_path and os.path.exists(segmentation.mask_file_path):
            try:
                os.remove(segmentation.mask_file_path)
            except OSError:
                pass
        db.delete(segmentation)

    # delete file fisik
    if photo.file_path and os.path.exists(photo.file_path):
        try:
            os.remove(photo.file_path)
        except OSError:
            pass

    db.delete(photo)
    db.commit()