import os
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import VideoOutputSegmentation, StreetPhoto, User
from app.schemas.video_output_segmentation import (
    VideoOutputSegmentationCreate,
    VideoOutputSegmentationUpdate,
    VideoOutputSegmentationResponse
)
from app.routers.auth import get_current_user
from app.db.enums import ProcessingStatus

# background task
from fastapi import BackgroundTasks
from app.service.ai_service import process_video_with_ai_task

router = APIRouter(prefix="/video-output-segmentations", tags=["Video Output Segmentations"])

# 1. CREATE
@router.post("/", response_model=VideoOutputSegmentationResponse, status_code=status.HTTP_201_CREATED)
def create_video_output(
    data: VideoOutputSegmentationCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Validasi apakah photo_id ada di tabel street_photos
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == data.photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foto/Video dengan ID '{data.photo_id}' tidak ditemukan."
        )

    # Validasi duplikasi (relasi One-to-One)
    existing_output = db.query(VideoOutputSegmentation).filter(
        VideoOutputSegmentation.photo_id == data.photo_id
    ).first()
    
    if existing_output:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data video output untuk foto/video dengan ID '{data.photo_id}' sudah ada."
        )

    # Insert data
    video_output = VideoOutputSegmentation(**data.model_dump())
    db.add(video_output)
    db.commit()
    db.refresh(video_output)
    
    return video_output

@router.post("/{video_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_video_processing(
    video_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Cari data video di database
    video = db.query(StreetPhoto).filter(StreetPhoto.id == video_id).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Data video tidak ditemukan di database"
        )

    # 2. Pastikan file fisik masih benar-benar ada di server
    if not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="File fisik video sudah tidak ada di server, tidak bisa diproses ulang"
        )

    # 3. Hapus hasil output lama jika sebelumnya sempat tersimpan (menghindari duplikasi/error unique constraint)
    db.query(VideoOutputSegmentation).filter(
        VideoOutputSegmentation.photo_id == video_id
    ).delete(synchronize_session=False)

    # 4. Reset status menjadi QUEUED dan hapus pesan error sebelumnya
    video.processing_status = ProcessingStatus.QUEUED
    video.error_message = None
    db.commit()

    # 5. Jalankan ulang background job menggunakan data dari database
    background_tasks.add_task(process_video_with_ai_task, video.id, video.file_path)

    return {
        "status": "success",
        "message": "Proses ulang segmentasi video berhasil dimasukkan ke antrean",
        "video_id": str(video.id)
    }

# 2. READ ALL
@router.get("/", response_model=List[VideoOutputSegmentationResponse])
def get_all_video_outputs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(VideoOutputSegmentation).all()


# 3. READ BY ID
@router.get("/{output_id}", response_model=VideoOutputSegmentationResponse)
def get_video_output(
    output_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_output = db.query(VideoOutputSegmentation).filter(VideoOutputSegmentation.id == output_id).first()
    if not video_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data video output tidak ditemukan."
        )
    return video_output


# 4. UPDATE BY ID
@router.put("/{output_id}", response_model=VideoOutputSegmentationResponse)
def update_video_output(
    output_id: UUID,
    data: VideoOutputSegmentationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_output = db.query(VideoOutputSegmentation).filter(VideoOutputSegmentation.id == output_id).first()
    if not video_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data video output tidak ditemukan."
        )

    # Validasi ulang jika photo_id diubah
    if data.photo_id and data.photo_id != video_output.photo_id:
        photo = db.query(StreetPhoto).filter(StreetPhoto.id == data.photo_id).first()
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Foto/Video dengan ID '{data.photo_id}' tidak ditemukan."
            )
            
        existing_output = db.query(VideoOutputSegmentation).filter(VideoOutputSegmentation.photo_id == data.photo_id).first()
        if existing_output:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data video output untuk ID '{data.photo_id}' sudah ada."
            )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(video_output, key, value)

    db.commit()
    db.refresh(video_output)
    return video_output


# 5. DELETE BY ID
@router.delete("/{output_id}", status_code=status.HTTP_200_OK)
def delete_video_output(
    output_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    video_output = db.query(VideoOutputSegmentation).filter(VideoOutputSegmentation.id == output_id).first()
    if not video_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data video output tidak ditemukan."
        )

    db.delete(video_output)
    db.commit()
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "success",
            "message": "Data video output berhasil dihapus",
            "deleted_id": str(output_id)
        }
    )

@router.get("/by-photo/", include_in_schema=False)
@router.get("/by-photo", include_in_schema=False)
def get_video_output_segmentation_by_photo_empty(current_user: User = Depends(get_current_user)):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Photo ID masih kosong! Silakan sertakan UUID photo_id pada URL (contoh: /by-photo/{photo_id})."
    )

@router.get("/by-photo/{photo_id}", response_model=VideoOutputSegmentationResponse)
def get_video_output_segmentation_by_photo(
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

    video_output = db.query(VideoOutputSegmentation).filter(
        VideoOutputSegmentation.photo_id == photo_id
    ).first()
    
    if not video_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Hasil segmentasi untuk foto dengan ID '{photo_id}' belum ada."
        )
        
    return video_output