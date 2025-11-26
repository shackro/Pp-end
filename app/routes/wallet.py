from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletData, DepositRequest, WithdrawRequest, TransactionResponse
from app.core.security import get_current_user

router = APIRouter()

@router.get("/balance/", response_model=WalletData)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    if not wallet:
        # Create wallet if it doesn't exist
        wallet = Wallet(user_id=current_user.id, balance=0.0, equity=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return WalletData(
        id=wallet.id,
        user_id=wallet.user_id,
        balance=wallet.balance,
        equity=wallet.equity,
        currency=wallet.currency,
        created_at=wallet.created_at.isoformat() if wallet.created_at else datetime.utcnow().isoformat(),
        updated_at=wallet.updated_at.isoformat() if wallet.updated_at else datetime.utcnow().isoformat()
    )

@router.post("/deposit/", response_model=TransactionResponse)
async def deposit_funds(
    deposit_data: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if deposit_data.phone_number != current_user.phone_number:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0.0, equity=0.0)
        db.add(wallet)
    
    wallet.balance += deposit_data.amount
    wallet.equity += deposit_data.amount
    
    db.commit()
    db.refresh(wallet)
    
    # Log transaction
    from app.models.transaction import Transaction
    transaction = Transaction(
        user_id=current_user.id,
        type="deposit",
        amount=deposit_data.amount,
        description=f"Deposit of {deposit_data.amount} {wallet.currency}",
        status="completed"
    )
    db.add(transaction)
    db.commit()
    
    return TransactionResponse(
        success=True,
        message="Deposit successful",
        new_balance=wallet.balance,
        new_equity=wallet.equity,
        transaction_id=f"DEP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )

@router.post("/withdraw/", response_model=TransactionResponse)
async def withdraw_funds(
    withdraw_data: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if withdraw_data.phone_number != current_user.phone_number:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet or wallet.balance < withdraw_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    wallet.balance -= withdraw_data.amount
    wallet.equity -= withdraw_data.amount
    
    db.commit()
    db.refresh(wallet)
    
    # Log transaction
    from app.models.transaction import Transaction
    transaction = Transaction(
        user_id=current_user.id,
        type="withdrawal",
        amount=withdraw_data.amount,
        description=f"Withdrawal of {withdraw_data.amount} {wallet.currency}",
        status="completed"
    )
    db.add(transaction)
    db.commit()
    
    return TransactionResponse(
        success=True,
        message="Withdrawal successful",
        new_balance=wallet.balance,
        new_equity=wallet.equity,
        transaction_id=f"WD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    )
