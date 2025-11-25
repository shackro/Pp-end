from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.core.security import decode_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/activities", tags=["activities"])
security = HTTPBearer()

def get_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/", response_model=list[ActivityResponse])
def list_activities(current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    activities = db.query(Activity).filter(Activity.user_id == current_user.id).order_by(Activity.timestamp.desc()).all()
    return [ActivityResponse.from_orm(act) for act in activities]

# Optional: endpoint to add an activity
@router.post("/", response_model=ActivityResponse)
def create_activity(description: str, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    new_activity = Activity(
        user_id=current_user.id,
        description=description
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return ActivityResponse.from_orm(new_activity)
