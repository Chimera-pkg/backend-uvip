from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import PerceptionPrediction, User, StreetPhoto, SegmentationResult
from app.schemas.perception_prediction import PerceptionPredictionCreate, PerceptionPredictionResponse, PerceptionPredictionUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/perception-predictions", tags=["Perception Predictions"])

# @router.post("/", response_model=PerceptionPredictionResponse, status_code=status.HTTP_201_CREATED)
# def create_prediction(data: PerceptionPredictionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     prediction = PerceptionPrediction(**data.model_dump())
#     db.add(prediction)
#     db.commit()
#     db.refresh(prediction)
#     return prediction

@router.post("/", response_model=PerceptionPredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
    data: PerceptionPredictionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == data.photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foto dengan ID '{data.photo_id}' tidak ditemukan."
        )

    existing_prediction = db.query(PerceptionPrediction).filter(
        PerceptionPrediction.photo_id == data.photo_id
    ).first()
    
    if existing_prediction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hasil prediksi persepsi untuk foto dengan ID '{data.photo_id}' sudah ada."
        )

    if data.segmentation_id:
        segmentation = db.query(SegmentationResult).filter(
            SegmentationResult.id == data.segmentation_id
        ).first()
        
        if not segmentation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hasil segmentasi dengan ID '{data.segmentation_id}' tidak ditemukan."
            )
        
        if segmentation.photo_id != data.photo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hasil segmentasi ID '{data.segmentation_id}' bukan milik foto dengan ID '{data.photo_id}'."
            )

    prediction = PerceptionPrediction(**data.model_dump())
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    return prediction

@router.get("/", response_model=List[PerceptionPredictionResponse])
def list_predictions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(PerceptionPrediction).all()

@router.get("/{prediction_id}", response_model=PerceptionPredictionResponse)
def get_prediction(prediction_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prediction = db.query(PerceptionPrediction).filter(PerceptionPrediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediksi tidak ditemukan")
    return prediction

@router.put("/{prediction_id}", response_model=PerceptionPredictionResponse)
def update_prediction(prediction_id: UUID, data: PerceptionPredictionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prediction = db.query(PerceptionPrediction).filter(PerceptionPrediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediksi tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(prediction, key, val)
    db.commit()
    db.refresh(prediction)
    return prediction

@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prediction(prediction_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prediction = db.query(PerceptionPrediction).filter(PerceptionPrediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediksi tidak ditemukan")
    db.delete(prediction)
    db.commit()
    return None