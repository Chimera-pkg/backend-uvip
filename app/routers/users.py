# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from typing import List
# from uuid import UUID

# from app.db.database import get_db
# from app.db.models import User
# from app.schemas.user import UserResponse, UserUpdate
# from app.routers.auth import get_current_user

# router = APIRouter(prefix="/users", tags=["Users"])

# @router.get("/", response_model=List[UserResponse])
# def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     return db.query(User).all()

# @router.get("/{user_id}", response_model=UserResponse)
# def get_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User tidak ditemukan")
#     return user

# @router.put("/{user_id}", response_model=UserResponse)
# def update_user(user_id: UUID, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     user = db.query(User).filter(User.id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User tidak ditemukan")
#     for key, val in data.model_dump(exclude_unset=True).items():
#         setattr(user, key, val)
#     db.commit()
#     db.refresh(user)
#     return user

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserResponse, UserUpdate
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

# read all
@router.get("/", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(User).all()

# read by id
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user

# update user
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(user, key, val)
    db.commit()
    db.refresh(user)
    return user

# delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    # user gaboleh hapus diri sendiri
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun sendiri yang sedang aktif")

    db.delete(user)
    db.commit()
    return None


# ADMIN ONLY: Deaktivasi Account User (is_active = False)
@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Admin yang dapat menonaktifkan akun user."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User tidak ditemukan"
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin tidak dapat menonaktifkan akunnya sendiri yang sedang aktif."
        )

    target_user.is_active = False
    
    db.commit()
    db.refresh(target_user)
    
    return target_user

# ADMIN ONLY: Aktivasi Account User (is_active = True)
@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak! Hanya Admin yang dapat mengaktifkan akun user."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User tidak ditemukan"
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin tidak dapat mengaktifkan akunnya sendiri yang sedang aktif."
        )

    target_user.is_active = True
    
    db.commit()
    db.refresh(target_user)
    
    return target_user