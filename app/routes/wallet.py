# app/routes/wallet.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletResponse, DepositRequest, TransactionResponse, PnLData
from app.core.security import decode_token
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/wallet", tags=["wallet"])
security = HTTPBearer()

def get_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get("/balance/{phone_number}", response_model=WalletResponse)
def get_wallet_balance(phone_number: str, db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == db.query(User).filter(User.phone_number == phone_number).first().id).first()
    if not wallet:
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        wallet = Wallet(user_id=user.id, balance=0.0, equity=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet

@router.post("/deposit", response_model=TransactionResponse)
def deposit_funds(data: DepositRequest, current_user: User = Depends(get_user_from_token), db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0.0, equity=0.0)
        db.add(wallet)
    wallet.balance += data.amount
    wallet.equity += data.amount
    db.commit()
    db.refresh(wallet)
    return TransactionResponse(success=True, message="Deposit successful", new_balance=wallet.balance, new_equity=wallet.equity)

@app.get("/api/wallet/pnl", response_model=PnLData)
async def get_user_pnl(current_user: dict = Depends(get_current_user)):
    """Calculate user's overall PnL across active investments"""
    await update_investment_values(current_user["phone_number"])
    investments = load_data(USER_INVESTMENTS_FILE, default={})
    
    total_invested = 0
    total_current_value = 0
    
    for inv in investments.values():
        if inv["user_phone"] == current_user["phone_number"] and inv["status"] == "active":
            total_invested += inv.get("invested_amount", 0)
            total_current_value += inv.get("current_value", 0)
    
    if total_invested == 0:
        profit_loss = 0
        percentage = 0
        trend = "neutral"
    else:
        profit_loss = total_current_value - total_invested
        percentage = (profit_loss / total_invested) * 100
        trend = "up" if profit_loss >= 0 else "down"
    
    return PnLData(
        profit_loss=round(profit_loss, 2),
        percentage=round(percentage, 2),
        trend=trend
    )


