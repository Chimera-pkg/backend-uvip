import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import SegmentationResult, User, StreetPhoto, PerceptionPrediction
from app.schemas.segmentation_result import SegmentationResultCreate, SegmentationResultResponse, SegmentationResultUpdate
from app.routers.auth import get_current_user
from app.db.enums import ProcessingStatus

# background task
from fastapi import BackgroundTasks
from app.service.ai_service import process_photo_with_ai_task

router = APIRouter(prefix="/segmentation-results", tags=["Segmentation Results"])

# @router.post("/", response_model=SegmentationResultResponse, status_code=status.HTTP_201_CREATED)
# def create_segmentation(data: SegmentationResultCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     segmentation = SegmentationResult(**data.model_dump())
#     db.add(segmentation)
#     db.commit()
#     db.refresh(segmentation)
#     return segmentation

@router.post("/", response_model=SegmentationResultResponse, status_code=status.HTTP_201_CREATED)
def create_segmentation(
    data: SegmentationResultCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == data.photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foto dengan ID '{data.photo_id}' tidak ditemukan."
        )

    existing_segmentation = db.query(SegmentationResult).filter(
        SegmentationResult.photo_id == data.photo_id
    ).first()
    
    if existing_segmentation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hasil segmentasi untuk foto dengan ID '{data.photo_id}' sudah ada."
        )

    segmentation = SegmentationResult(**data.model_dump())
    db.add(segmentation)
    db.commit()
    db.refresh(segmentation)
    
    return segmentation

@router.post("/{photo_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_photo_processing(
    photo_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Cari data foto di database
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Data foto tidak ditemukan di database"
        )

    # 2. Pastikan file fisik foto masih benar-benar ada di server
    if not os.path.exists(photo.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="File fisik foto sudah tidak ada di server, tidak bisa diproses ulang"
        )

    # 3. Bersihkan hasil AI lama secara berurutan (Cascade Delete) agar tidak error duplikat
    # A. Hapus Perception Predictions & Shap Values terkait
    predictions = db.query(PerceptionPrediction).filter(
        PerceptionPrediction.photo_id == photo_id
    ).all()
    prediction_ids = [p.id for p in predictions]

    if prediction_ids:
        # Hapus SHAP values terlebih dahulu (anak dari prediction)
        db.query(ShapValue).filter(
            ShapValue.prediction_id.in_(prediction_ids)
        ).delete(synchronize_session=False)
        
        # Hapus Prediction (anak dari segmentation & photo)
        db.query(PerceptionPrediction).filter(
            PerceptionPrediction.id.in_(prediction_ids)
        ).delete(synchronize_session=False)

    # B. Hapus Segmentation Result lama
    db.query(SegmentationResult).filter(
        SegmentationResult.photo_id == photo_id
    ).delete(synchronize_session=False)

    # 4. Reset status menjadi QUEUED dan hapus log error sebelumnya
    photo.processing_status = ProcessingStatus.QUEUED
    photo.error_message = None
    db.commit()

    # 5. Jalankan ulang background job untuk foto
    background_tasks.add_task(process_photo_with_ai_task, photo.id, photo.file_path)

    return {
        "status": "success",
        "message": "Proses ulang segmentasi foto berhasil dimasukkan ke antrean",
        "photo_id": str(photo.id)
    }

@router.get("/", response_model=List[SegmentationResultResponse])
def list_segmentations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SegmentationResult).all()

@router.get("/{segmentation_id}", response_model=SegmentationResultResponse)
def get_segmentation(segmentation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    segmentation = db.query(SegmentationResult).filter(SegmentationResult.id == segmentation_id).first()
    if not segmentation:
        raise HTTPException(status_code=404, detail="Hasil segmentasi tidak ditemukan")
    return segmentation

@router.put("/{segmentation_id}", response_model=SegmentationResultResponse)
def update_segmentation(segmentation_id: UUID, data: SegmentationResultUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    segmentation = db.query(SegmentationResult).filter(SegmentationResult.id == segmentation_id).first()
    if not segmentation:
        raise HTTPException(status_code=404, detail="Hasil segmentasi tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(segmentation, key, val)
    db.commit()
    db.refresh(segmentation)
    return segmentation

@router.delete("/{segmentation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_segmentation(segmentation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    segmentation = db.query(SegmentationResult).filter(SegmentationResult.id == segmentation_id).first()
    if not segmentation:
        raise HTTPException(status_code=404, detail="Hasil segmentasi tidak ditemukan")
    db.delete(segmentation)
    db.commit()
    return None

@router.get("/by-photo/", include_in_schema=False)
@router.get("/by-photo", include_in_schema=False)
def get_segmentation_by_photo_empty(current_user: User = Depends(get_current_user)):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Photo ID masih kosong! Silakan sertakan UUID photo_id pada URL (contoh: /by-photo/{photo_id})."
    )

@router.get("/by-photo/{photo_id}", response_model=SegmentationResultResponse)
def get_segmentation_by_photo(
    photo_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if photo_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo ID masih kosong atau tidak valid."
        )
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foto dengan ID '{photo_id}' tidak ditemukan."
        )

    segmentation = db.query(SegmentationResult).filter(
        SegmentationResult.photo_id == photo_id
    ).first()
    
    if not segmentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Hasil segmentasi untuk foto dengan ID '{photo_id}' belum ada."
        )
        
    return segmentation