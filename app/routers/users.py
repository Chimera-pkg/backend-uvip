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

from fastapi import APIRouter, Depends, HTTPException, status, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List
import uuid
from uuid import UUID

from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserResponse, UserUpdate
from app.routers.auth import get_current_user
import os

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

PROFILE_UPLOAD_DIR = "uploads/profiles"
os.makedirs(PROFILE_UPLOAD_DIR, exist_ok=True)

@router.patch("/me/avatar", status_code=status.HTTP_200_OK)
async def update_profile_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint untuk mengunggah atau memperbarui foto profil user yang sedang login.
    """
    # 1. Validasi Format File Gambar
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Format file tidak didukung! Gunakan .jpg, .jpeg, .png, atau .webp"
        )

    # 2. Hapus foto profil lama jika ada (opsional, agar storage server tidak penuh sampah)
    if current_user.profile_file_path and os.path.exists(current_user.profile_file_path):
        try:
            os.remove(current_user.profile_file_path)
        except Exception:
            pass # Lewati jika file lama gagal dihapus

    # 3. Buat nama file unik menggunakan UUID user / random UUID
    saved_filename = f"user_{current_user.id}_{uuid.uuid4()}{file_ext}"
    relative_file_path = os.path.join(PROFILE_UPLOAD_DIR, saved_filename).replace("\\", "/")

    # 4. Simpan file fisik ke server
    try:
        contents = await file.read()
        with open(relative_file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file foto profil: {str(e)}")

    # 5. Update record database pada user yang sedang login
    current_user.profile_filename = file.filename
    current_user.profile_file_path = relative_file_path
    
    db.commit()
    db.refresh(current_user)

    return {
        "status": "success",
        "message": "Foto profil berhasil diperbarui",
        "profile_filename": current_user.profile_filename,
        "profile_file_path": current_user.profile_file_path
    }