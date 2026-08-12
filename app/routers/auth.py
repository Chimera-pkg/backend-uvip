from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse
from app.schemas.user import UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Public Endpoint: Register
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar!")
    
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Public Endpoint: Login
@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email atau password salah!")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Akun tidak aktif.")
    
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}

# Global Dependency: Proteksi Token untuk endpoint terproteksi
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau kadaluwarsa",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user