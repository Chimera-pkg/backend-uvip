from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import OfflineSyncQueue, User
from app.schemas.offline_sync_queue import OfflineSyncQueueCreate, OfflineSyncQueueResponse, OfflineSyncQueueUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/offline-sync-queues", tags=["Offline Sync Queue"])

@router.post("/", response_model=OfflineSyncQueueResponse, status_code=status.HTTP_201_CREATED)
def create_sync_queue(data: OfflineSyncQueueCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue_item = OfflineSyncQueue(**data.model_dump(), user_id=current_user.id)
    db.add(queue_item)
    db.commit()
    db.refresh(queue_item)
    return queue_item

@router.get("/", response_model=List[OfflineSyncQueueResponse])
def list_sync_queues(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(OfflineSyncQueue).all()

@router.get("/{queue_id}", response_model=OfflineSyncQueueResponse)
def get_sync_queue(queue_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue_item = db.query(OfflineSyncQueue).filter(OfflineSyncQueue.id == queue_id).first()
    if not queue_item:
        raise HTTPException(status_code=404, detail="Item antrean sync tidak ditemukan")
    return queue_item

@router.put("/{queue_id}", response_model=OfflineSyncQueueResponse)
def update_sync_queue(queue_id: UUID, data: OfflineSyncQueueUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue_item = db.query(OfflineSyncQueue).filter(OfflineSyncQueue.id == queue_id).first()
    if not queue_item:
        raise HTTPException(status_code=404, detail="Item antrean sync tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(queue_item, key, val)
    db.commit()
    db.refresh(queue_item)
    return queue_item

@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sync_queue(queue_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    queue_item = db.query(OfflineSyncQueue).filter(OfflineSyncQueue.id == queue_id).first()
    if not queue_item:
        raise HTTPException(status_code=404, detail="Item antrean sync tidak ditemukan")
    db.delete(queue_item)
    db.commit()
    return None