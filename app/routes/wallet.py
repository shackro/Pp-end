from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.wallet import Wallet
from app.models.user import User
from app.schemas.wallet import WalletResponse, DepositRequest, TransactionResponse

router = APIRouter()

@router.get("/balance", response_model=WalletResponse)
async def get_wallet_balance(db: Session = Depends(get_db)):
    # For demo, get first user's wallet
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    
    # Create wallet if doesn't exist
    if not wallet:
        wallet = Wallet(
            user_id=user.id,
            balance=25000.0,
            equity=32500.0
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return wallet

@router.post("/deposit", response_model=TransactionResponse)
async def deposit_funds(deposit_data: DepositRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id)
        db.add(wallet)
    
    wallet.balance += deposit_data.amount
    wallet.equity += deposit_data.amount
    
    db.commit()
    db.refresh(wallet)
    
    return TransactionResponse(
        success=True,
        message="Deposit successful",
        new_balance=wallet.balance,
        new_equity=wallet.equity
    )