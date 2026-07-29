from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import StreetPhoto, User
from app.schemas.street_photo import StreetPhotoCreate, StreetPhotoResponse, StreetPhotoUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/street-photos", tags=["Street Photos"])

@router.post("/", response_model=StreetPhotoResponse, status_code=status.HTTP_201_CREATED)
def create_photo(data: StreetPhotoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = StreetPhoto(**data.model_dump(), uploaded_by=current_user.id)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo

@router.get("/", response_model=List[StreetPhotoResponse])
def list_photos(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(StreetPhoto).all()

@router.get("/{photo_id}", response_model=StreetPhotoResponse)
def get_photo(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    return photo

@router.put("/{photo_id}", response_model=StreetPhotoResponse)
def update_photo(photo_id: UUID, data: StreetPhotoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(photo, key, val)
    db.commit()
    db.refresh(photo)
    return photo

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    photo = db.query(StreetPhoto).filter(StreetPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    db.delete(photo)
    db.commit()
    return None