# app/routes/wallet.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletResponse, DepositRequest, TransactionResponse
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
