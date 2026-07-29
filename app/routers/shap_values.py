from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import ShapValue, User
from app.schemas.shap_value import ShapValueCreate, ShapValueResponse, ShapValueUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/shap-values", tags=["SHAP Values"])

@router.post("/", response_model=ShapValueResponse, status_code=status.HTTP_201_CREATED)
def create_shap_value(data: ShapValueCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shap_val = ShapValue(**data.model_dump())
    db.add(shap_val)
    db.commit()
    db.refresh(shap_val)
    return shap_val

@router.get("/", response_model=List[ShapValueResponse])
def list_shap_values(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ShapValue).all()

@router.get("/{shap_id}", response_model=ShapValueResponse)
def get_shap_value(shap_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shap_val = db.query(ShapValue).filter(ShapValue.id == shap_id).first()
    if not shap_val:
        raise HTTPException(status_code=404, detail="SHAP Value tidak ditemukan")
    return shap_val

@router.put("/{shap_id}", response_model=ShapValueResponse)
def update_shap_value(shap_id: UUID, data: ShapValueUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shap_val = db.query(ShapValue).filter(ShapValue.id == shap_id).first()
    if not shap_val:
        raise HTTPException(status_code=404, detail="SHAP Value tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(shap_val, key, val)
    db.commit()
    db.refresh(shap_val)
    return shap_val

@router.delete("/{shap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shap_value(shap_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shap_val = db.query(ShapValue).filter(ShapValue.id == shap_id).first()
    if not shap_val:
        raise HTTPException(status_code=404, detail="SHAP Value tidak ditemukan")
    db.delete(shap_val)
    db.commit()
    return None