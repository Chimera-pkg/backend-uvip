from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import SimulationSession, User
from app.schemas.simulation_session import SimulationSessionCreate, SimulationSessionResponse, SimulationSessionUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/simulation-sessions", tags=["Simulation Sessions"])

@router.post("/", response_model=SimulationSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(data: SimulationSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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