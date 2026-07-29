from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import MissionAssignment, User
from app.schemas.mission_assignment import MissionAssignmentCreate, MissionAssignmentResponse, MissionAssignmentUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/mission-assignments", tags=["Mission Assignments"])

@router.post("/", response_model=MissionAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(data: MissionAssignmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignment = MissionAssignment(**data.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/", response_model=List[MissionAssignmentResponse])
def list_assignments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(MissionAssignment).all()

@router.get("/{assignment_id}", response_model=MissionAssignmentResponse)
def get_assignment(assignment_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignment = db.query(MissionAssignment).filter(MissionAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment tidak ditemukan")
    return assignment

@router.put("/{assignment_id}", response_model=MissionAssignmentResponse)
def update_assignment(assignment_id: UUID, data: MissionAssignmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignment = db.query(MissionAssignment).filter(MissionAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(assignment, key, val)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    assignment = db.query(MissionAssignment).filter(MissionAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment tidak ditemukan")
    db.delete(assignment)
    db.commit()
    return None