from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models.transaction import Investment
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.investment import InvestmentCreate, InvestmentResponse
from app.core.security import decode_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/investments", tags=["investments"])
security = HTTPBearer()

# Utility function to get the current user from token
def get_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Endpoint to buy an investment
@router.post("/buy", response_model=InvestmentResponse)
def buy_investment(data: InvestmentCreate, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet or wallet.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    invested_amount = data.amount
    entry_price = 1.0  # placeholder for real asset price
    units = invested_amount / entry_price

    investment = Investment(
        user_id=current_user.id,
        asset_id=data.asset_id or "",
        asset_name=data.asset_name or "",
        invested_amount=invested_amount,
        current_value=invested_amount,
        units=units,
        entry_price=entry_price,
        current_price=entry_price,
        profit_loss=0.0,
        profit_loss_percentage=0.0,
        status="active",
        created_at=datetime.utcnow(),
        completion_time=(datetime.utcnow() + timedelta(hours=24))
    )

    db.add(investment)
    wallet.balance -= invested_amount
    db.commit()
    db.refresh(investment)
    db.refresh(wallet)

    return InvestmentResponse.from_orm(investment)

# Endpoint to get all investments of the current user
@router.get("/my", response_model=list[InvestmentResponse])
def get_my_investments(current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    investments = db.query(Investment).filter(Investment.user_id == current_user.id).all()
    return [InvestmentResponse.from_orm(inv) for inv in investments]

# Optional: endpoint to get active investments only
@router.get("/active", response_model=list[InvestmentResponse])
def get_active_investments(current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id,
        Investment.status == "active"
    ).all()
    return [InvestmentResponse.from_orm(inv) for inv in investments]
