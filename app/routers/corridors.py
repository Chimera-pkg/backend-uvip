# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List
# from uuid import UUID

# from app.db.database import get_db
# from app.db.models import Corridor, User
# from app.schemas.corridor import CorridorCreate, CorridorResponse, CorridorUpdate
# from app.routers.auth import get_current_user

# router = APIRouter(prefix="/corridors", tags=["Corridors"])

# @router.post("/", response_model=CorridorResponse)
# def create_corridor(data: CorridorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     corridor = Corridor(**data.model_dump(), created_by=current_user.id)
#     db.add(corridor)
#     db.commit()
#     db.refresh(corridor)
#     return corridor

# @router.get("/", response_model=List[CorridorResponse])
# def list_corridors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return db.query(Corridor).all()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from geoalchemy2 import WKTElement
from app.db.enums import UserRole
from app.db.database import get_db
from app.db.models import Corridor, User
from app.schemas.corridor import CorridorCreate, CorridorResponse, CorridorUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/corridors", tags=["Corridors"])

# 1. CREATE
@router.post("/", response_model=CorridorResponse, status_code=status.HTTP_201_CREATED)
def create_corridor(data: CorridorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed_roles = [UserRole.ADMIN, UserRole.PLANNER]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Admin dan Planner yang dapat membuat koridor baru."
        )

    corridor_data = data.model_dump()
    
    if corridor_data.get("geom"):
        corridor_data["geom"] = WKTElement(corridor_data["geom"], srid=4326)

    corridor = Corridor(**data.model_dump(), created_by=current_user.id)
    db.add(corridor)
    db.commit()
    db.refresh(corridor)
    return corridor

# 2. READ ALL
@router.get("/", response_model=List[CorridorResponse])
def list_corridors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Corridor).all()

# 3. READ BY ID
@router.get("/{corridor_id}", response_model=CorridorResponse)
def get_corridor(corridor_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    corridor = db.query(Corridor).filter(Corridor.id == corridor_id).first()
    if not corridor:
        raise HTTPException(status_code=404, detail="Koridor tidak ditemukan")
    return corridor

# 4. UPDATE BY ID
@router.put("/{corridor_id}", response_model=CorridorResponse)
def update_corridor(corridor_id: UUID, data: CorridorUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    corridor = db.query(Corridor).filter(Corridor.id == corridor_id).first()
    if not corridor:
        raise HTTPException(status_code=404, detail="Koridor tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(corridor, key, val)
    db.commit()
    db.refresh(corridor)
    return corridor

# 5. DELETE BY ID
@router.delete("/{corridor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_corridor(corridor_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    corridor = db.query(Corridor).filter(Corridor.id == corridor_id).first()
    if not corridor:
        raise HTTPException(status_code=404, detail="Koridor tidak ditemukan")
    db.delete(corridor)
    db.commit()
    return None