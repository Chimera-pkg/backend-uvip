from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.enums import UserRole
from app.db.database import get_db
from app.db.models import SimulationSession, User, Corridor, StreetPhoto, PerceptionPrediction
from app.schemas.simulation_session import SimulationSessionCreate, SimulationSessionResponse, SimulationSessionUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/simulation-sessions", tags=["Simulation Sessions"])

# @router.post("/", response_model=SimulationSessionResponse, status_code=status.HTTP_201_CREATED)
# def create_session(data: SimulationSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     session = SimulationSession(**data.model_dump(), created_by=current_user.id)
#     db.add(session)
#     db.commit()
#     db.refresh(session)
#     return session
@router.post("/", response_model=SimulationSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    data: SimulationSessionCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    allowed_roles = [UserRole.PLANNER, UserRole.ADMIN]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Planner yang dapat membuat sesi simulasi baru."
        )

    if data.corridor_id:
        corridor = db.query(Corridor).filter(Corridor.id == data.corridor_id).first()
        if not corridor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Koridor dengan ID '{data.corridor_id}' tidak ditemukan."
            )

    if data.base_photo_id:
        photo = db.query(StreetPhoto).filter(StreetPhoto.id == data.base_photo_id).first()
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Foto dasar dengan ID '{data.base_photo_id}' tidak ditemukan."
            )

    if data.base_prediction_id:
        prediction = db.query(PerceptionPrediction).filter(
            PerceptionPrediction.id == data.base_prediction_id
        ).first()
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prediksi dasar dengan ID '{data.base_prediction_id}' tidak ditemukan."
            )

    session = SimulationSession(**data.model_dump(), created_by=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

@router.get("/", response_model=List[SimulationSessionResponse])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SimulationSession).all()

@router.get("/{session_id}", response_model=SimulationSessionResponse)
def get_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Simulation session tidak ditemukan")
    return session

@router.put("/{session_id}", response_model=SimulationSessionResponse)
def update_session(session_id: UUID, data: SimulationSessionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Simulation session tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(session, key, val)
    db.commit()
    db.refresh(session)
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Simulation session tidak ditemukan")
    db.delete(session)
    db.commit()
    return None

@router.patch("/{session_id}", response_model=SimulationSessionResponse)
def patch_session_adjustments(
    session_id: UUID,
    data: SimulationSessionUpdate,  # semua field di schema update bersifat Optional
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(SimulationSession).filter(SimulationSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Sesi simulasi tidak ditemukan"
        )

    allowed_roles = [UserRole.PLANNER, UserRole.ADMIN]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Planner yang dapat mengubah data simulasi."
        )

    # exclude_unset=True memastikan hanya field yang dikirim dari slider yang diupdate
    update_data = data.model_dump(exclude_unset=True)
    
    for key, val in update_data.items():
        setattr(session, key, val)

    db.commit()
    db.refresh(session)
    return session