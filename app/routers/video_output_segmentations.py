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