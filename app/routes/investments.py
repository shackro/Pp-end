# app/routes/investments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transaction import Investment
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.investment import InvestmentCreate, InvestmentResponse
from app.core.security import decode_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/investments", tags=["investments"])
security = HTTPBearer()

def get_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/buy", response_model=InvestmentResponse)
def buy_investment(data: InvestmentCreate, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    # amount is in KES in this API
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet or wallet.balance < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    # For now we treat current_price = amount / units (units will be computed from an asset price)
    # If asset_id provided, you should compute units from real price; here we store as 1 unit = invested amount
    invested_amount = data.amount
    # Simulate entry/current price equal to 1 for simple units calculation to avoid division by zero
    entry_price = 1.0
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

@router.get("/my", response_model=list[InvestmentResponse])
def get_my_investments(current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    invs = db.query(Investment).filter(Investment.user_id == current_user.id).all()
    return [InvestmentResponse.from_orm(i) for i in invs]
