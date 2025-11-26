from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone_number: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    created_at: str
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    success: bool
    message: str
    access_token: str
    token_type: str
    user: UserResponse

class TokenRefreshResponse(BaseModel):
    access: str
    refresh: str
