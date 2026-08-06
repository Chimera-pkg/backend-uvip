from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.enums import UserRole
from app.db.database import get_db
from app.db.models import ModelRegistry, User
from app.schemas.model_registry import ModelRegistryCreate, ModelRegistryResponse, ModelRegistryUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/model-registries", tags=["Model Registries"])

# @router.post("/", response_model=ModelRegistryResponse, status_code=status.HTTP_201_CREATED)
# def create_model_registry(data: ModelRegistryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     model_reg = ModelRegistry(**data.model_dump())
#     db.add(model_reg)
#     db.commit()
#     db.refresh(model_reg)
#     return model_reg

@router.post("/", response_model=ModelRegistryResponse, status_code=status.HTTP_201_CREATED)
def create_model_registry(
    data: ModelRegistryCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Admin yang dapat mendaftarkan model AI baru."
        )

    if data.is_active:
        db.query(ModelRegistry).filter(
            ModelRegistry.model_type == data.model_type,
            ModelRegistry.is_active == True
        ).update({"is_active": False}, synchronize_session=False)

    new_model = ModelRegistry(**data.model_dump())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return new_model

@router.get("/", response_model=List[ModelRegistryResponse])
def list_model_registries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ModelRegistry).all()

@router.get("/{model_id}", response_model=ModelRegistryResponse)
def get_model_registry(model_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    model_reg = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model_reg:
        raise HTTPException(status_code=404, detail="Model Registry tidak ditemukan")
    return model_reg

@router.put("/{model_id}", response_model=ModelRegistryResponse)
def update_model_registry(model_id: UUID, data: ModelRegistryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    model_reg = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model_reg:
        raise HTTPException(status_code=404, detail="Model Registry tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(model_reg, key, val)
    db.commit()
    db.refresh(model_reg)
    return model_reg

@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_registry(model_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    model_reg = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model_reg:
        raise HTTPException(status_code=404, detail="Model Registry tidak ditemukan")
    db.delete(model_reg)
    db.commit()
    return None

@router.patch("/{model_id}/activate", response_model=ModelRegistryResponse)
def activate_model(
    model_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Admin yang dapat mengaktifkan model AI.",
        )

    target_model = (
        db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    )
    if not target_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model Registry dengan ID '{model_id}' tidak ditemukan.",
        )

    # nonaktifkan semua model lain yang memiliki model_type yang sama
    db.query(ModelRegistry).filter(
        ModelRegistry.model_type == target_model.model_type,
        ModelRegistry.id != model_id,
    ).update({"is_active": False}, synchronize_session=False)

    target_model.is_active = True

    db.commit()
    db.refresh(target_model)

    return target_model