from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import SimulationResult, User, SimulationSession
from app.schemas.simulation_result import SimulationResultCreate, SimulationResultResponse, SimulationResultUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/simulation-results", tags=["Simulation Results"])

@router.post("/", response_model=SimulationResultResponse, status_code=status.HTTP_201_CREATED)
def create_result(data: SimulationResultCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    simulation_session = db.query(SimulationSession).filter(SimulationSession.id == data.session_id).first()
    if not simulation_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulasi Sesi dengan ID '{data.session_id}' tidak ditemukan."
        )

    result = SimulationResult(**data.model_dump())
    db.add(result)
    db.commit()
    db.refresh(result)
    return result

@router.get("/", response_model=List[SimulationResultResponse])
def list_results(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SimulationResult).all()

@router.get("/{result_id}", response_model=SimulationResultResponse)
def get_result(result_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(SimulationResult).filter(SimulationResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil simulasi tidak ditemukan")
    return result

@router.put("/{result_id}", response_model=SimulationResultResponse)
def update_result(result_id: UUID, data: SimulationResultUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(SimulationResult).filter(SimulationResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil simulasi tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(result, key, val)
    db.commit()
    db.refresh(result)
    return result

@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(result_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = db.query(SimulationResult).filter(SimulationResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Hasil simulasi tidak ditemukan")
    db.delete(result)
    db.commit()
    return None