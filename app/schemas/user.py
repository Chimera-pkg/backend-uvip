from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from uuid import UUID
from datetime import datetime
from app.db.enums import UserRole

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: UUID
    name: str
    profile_filename: Optional[str] = None
    profile_file_path: Optional[str] = None
    email: EmailStr
    role: UserRole
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    old_password: str
    new_password: str