from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Schema for creating a new activity
class ActivityCreate(BaseModel):
    type: str
    user_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

# Schema for reading activity from DB
class ActivityResponse(ActivityCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
