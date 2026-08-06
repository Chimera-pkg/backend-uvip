from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import SegmentationResult, User, StreetPhoto
from app.schemas.segmentation_result import SegmentationResultCreate, SegmentationResultResponse, SegmentationResultUpdate
from app.routers.auth import get_current_user

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