from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db.enums import UserRole
from app.db.database import get_db
from app.db.models import MissionAssignment, User, SurveyMission
from app.schemas.mission_assignment import MissionAssignmentCreate, MissionAssignmentResponse, MissionAssignmentUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/mission-assignments", tags=["Mission Assignments"])

@router.post("/", response_model=MissionAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(data: MissionAssignmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed_roles = [UserRole.ADMIN, UserRole.PLANNER]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Admin dan Planner yang dapat membuat mission assignment baru."
        )

    mission = db.query(SurveyMission).filter(SurveyMission.id == data.mission_id).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Mission tidak ditemukan."
        )

    assigned_user = db.query(User).filter(User.id == data.user_id).first()
    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User yang akan ditugaskan tidak ditemukan."
        )
    
    if assigned_user.role != UserRole.SURVEYOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{assigned_user.name}' bukan ber-role Surveyor (Role saat ini: {assigned_user.role.value}). Misi hanya dapat ditugaskan kepada Surveyor."
        )

    existing_assignment = db.query(MissionAssignment).filter(
        MissionAssignment.mission_id == data.mission_id,
        MissionAssignment.user_id == data.user_id
    ).first()

    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Surveyor ini sudah ditugaskan pada misi tersebut."
        )

    assignment_data = data.model_dump(exclude_none=True)
    assignment = MissionAssignment(**assignment_data)
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