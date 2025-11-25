# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.database import get_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    hashed = get_password_hash(user_data.password)
    user = User(name=user_data.name, email=user_data.email, phone_number=user_data.phone_number, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.from_orm(user))

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.from_orm(user))

@router.get("/user/")
async def get_user(current_user: dict = Depends(get_current_user)):
    if current_user:
        return {"email": current_user.get("email")}
    return {"error": "User not found"}

# simple user info endpoint - uses Bearer token decoding in main
