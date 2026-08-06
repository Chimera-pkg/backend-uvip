from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import BatchUploadJob, User, SurveyMission
from app.schemas.batch_upload_job import BatchUploadJobCreate, BatchUploadJobResponse, BatchUploadJobUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/batch-upload-jobs", tags=["Batch Upload Jobs"])

@router.post("/", response_model=BatchUploadJobResponse, status_code=status.HTTP_201_CREATED)
def create_batch_job(data: BatchUploadJobCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    mission = db.query(SurveyMission).filter(SurveyMission.id == data.mission_id).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey Mission dengan ID '{data.mission_id}' tidak ditemukan."
        )

    job = BatchUploadJob(**data.model_dump(), created_by=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/", response_model=List[BatchUploadJobResponse])
def list_batch_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(BatchUploadJob).all()

@router.get("/{job_id}", response_model=BatchUploadJobResponse)
def get_batch_job(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(BatchUploadJob).filter(BatchUploadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Batch Job tidak ditemukan")
    return job

@router.put("/{job_id}", response_model=BatchUploadJobResponse)
def update_batch_job(job_id: UUID, data: BatchUploadJobUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(BatchUploadJob).filter(BatchUploadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Batch Job tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(job, key, val)
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_job(job_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(BatchUploadJob).filter(BatchUploadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Batch Job tidak ditemukan")
    db.delete(job)
    db.commit()
    return None