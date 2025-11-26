from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.schemas.activity import UserActivity
from app.core.security import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserActivity])
async def get_my_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: Optional[int] = Query(1, ge=1),
    activity_type: Optional[str] = None,
    limit: Optional[int] = Query(20, ge=1, le=100)
):
    query = db.query(Activity).filter(Activity.user_id == current_user.id)
    
    if activity_type:
        query = query.filter(Activity.type == activity_type)
    
    activities = query.order_by(Activity.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    activity_list = []
    for act in activities:
        activity_list.append(UserActivity(
            id=act.id,
            user_phone=current_user.phone_number,
            activity_type=act.type,
            amount=act.data.get("amount", 0) if act.data else 0,
            description=act.data.get("description", "") if act.data else "",
            timestamp=act.created_at.isoformat() if act.created_at else datetime.utcnow().isoformat(),
            status="completed"
        ))
    
    return activity_list
