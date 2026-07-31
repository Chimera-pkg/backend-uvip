from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from app.db.database import get_db
from app.db.models import SurveyMission, User
from app.schemas.survey_mission import SurveyMissionCreate, SurveyMissionResponse, SurveyMissionUpdate
from app.routers.auth import get_current_user
from app.db.enums import MissionStatus

router = APIRouter(prefix="/survey-missions", tags=["Survey Missions"])

@router.post("/", response_model=SurveyMissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(data: SurveyMissionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = SurveyMission(**data.model_dump(), created_by=current_user.id)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission

@router.get("/", response_model=List[SurveyMissionResponse])
def list_missions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SurveyMission).all()

@router.get("/{mission_id}", response_model=SurveyMissionResponse)
def get_mission(mission_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission tidak ditemukan")
    return mission

@router.put("/{mission_id}", response_model=SurveyMissionResponse)
def update_mission(mission_id: UUID, data: SurveyMissionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(mission, key, val)
    db.commit()
    db.refresh(mission)
    return mission

@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(mission_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission tidak ditemukan")
    db.delete(mission)
    db.commit()
    return None

@router.patch("/{mission_id}/pause", response_model=SurveyMissionResponse)
def pause_mission(mission_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission tidak ditemukan")
    
    if mission.status == MissionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Mission yang sudah selesai tidak dapat di-pause")
    
    mission.status = MissionStatus.PAUSED
    db.commit()
    db.refresh(mission)
    return mission

@router.patch("/{mission_id}/resume", response_model=SurveyMissionResponse)
def resume_mission(mission_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission tidak ditemukan")
    
    if mission.status == MissionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Mission yang sudah selesai tidak dapat diaktifkan kembali")
    
    mission.status = MissionStatus.ACTIVE
    db.commit()
    db.refresh(mission)
    return mission

@router.patch("/{mission_id}/complete", response_model=SurveyMissionResponse)
def complete_mission(mission_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission tidak ditemukan")
    
    mission.status = MissionStatus.COMPLETED
    mission.completed_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(mission)
    return mission