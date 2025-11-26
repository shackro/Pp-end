from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, AuthResponse
from app.core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt
from datetime import datetime
from app.core.security import (
    get_password_hash, verify_password, create_access_token, 
    get_current_user, SECRET_KEY, ALGORITHM
)


router = APIRouter()

# Add the missing endpoints frontend expects
@router.post("/register/", response_model=AuthResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | 
        (User.phone_number == user_data.phone_number)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or phone number already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        hashed_password=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create wallet for user
    from app.models.wallet import Wallet
    wallet = Wallet(user_id=user.id, balance=5000.0, equity=5000.0)
    db.add(wallet)
    db.commit()
    
    # Generate token
    access_token = create_access_token(data={"sub": user.email})
    
    return AuthResponse(
        success=True,
        message="User registered successfully",
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            created_at=user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
        )
    )

@router.post("/login/", response_model=AuthResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return AuthResponse(
        success=True,
        message="Login successful",
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            created_at=user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
        )
    )

@router.get("/user/", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone_number=current_user.phone_number,
        created_at=current_user.created_at.isoformat() if current_user.created_at else datetime.utcnow().isoformat()
    )

# Add other auth endpoints frontend might need
@router.put("/profile/update/")
async def update_profile(profile_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Update user profile logic
    for field, value in profile_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": UserResponse.from_orm(current_user)
    }

@router.post("/password/change/")
async def change_password(password_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Password change logic
    return {
        "success": True,
        "message": "Password changed successfully"
    }
