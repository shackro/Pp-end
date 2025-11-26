from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.investment import Investment
from app.models.wallet import Wallet
from app.schemas.investment import InvestmentRequest, UserInvestment, Asset
from app.core.security import get_current_user
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/assets/", response_model=List[Asset])
async def get_assets():
    """Get all available assets for investment"""
    # Use your existing generate_dynamic_prices function
    from app.main import generate_dynamic_prices
    return await generate_dynamic_prices()

@router.get("/my-investments/", response_model=List[UserInvestment])
async def get_my_investments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investments = db.query(Investment).filter(
        Investment.user_id == current_user.id
    ).all()
    
    investment_list = []
    for inv in investments:
        investment_list.append(UserInvestment(
            id=inv.id,
            user=inv.user_id,
            asset_id=inv.asset_id or "",
            asset_name=inv.asset_name or "",
            invested_amount=inv.invested_amount,
            current_value=inv.current_value,
            units=inv.units,
            entry_price=inv.entry_price,
            current_price=inv.current_price,
            profit_loss=inv.profit_loss,
            profit_loss_percentage=inv.profit_loss_percentage,
            status=inv.status,
            created_at=inv.created_at.isoformat() if inv.created_at else datetime.utcnow().isoformat(),
            completion_time=inv.completion_time.isoformat() if inv.completion_time else None
        ))
    
    return investment_list

@router.post("/buy/", response_model=dict)
async def buy_investment(
    investment_data: InvestmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if investment_data.phone_number != current_user.phone_number:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Check wallet balance
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet or wallet.balance < investment_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Get asset details
    from app.main import generate_dynamic_prices
    assets = await generate_dynamic_prices()
    asset = next((a for a in assets if a["id"] == investment_data.asset_id), None)
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check minimum investment
    if investment_data.amount < asset["min_investment"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum investment is {asset['min_investment']} {asset.get('currency', 'KES')}"
        )
    
    # Calculate units
    units = investment_data.amount / asset["current_price"]
    
    # Create investment
    investment = Investment(
        user_id=current_user.id,
        asset_id=investment_data.asset_id,
        asset_name=asset["name"],
        invested_amount=investment_data.amount,
        current_value=investment_data.amount,
        units=units,
        entry_price=asset["current_price"],
        current_price=asset["current_price"],
        profit_loss=0.0,
        profit_loss_percentage=0.0,
        status="active",
        completion_time=datetime.utcnow() + timedelta(hours=asset["duration"])
    )
    
    # Update wallet
    wallet.balance -= investment_data.amount
    
    db.add(investment)
    db.commit()
    db.refresh(investment)
    db.refresh(wallet)
    
    # Log activity
    from app.models.activity import Activity
    activity = Activity(
        user_id=current_user.id,
        type="investment",
        data={
            "asset": asset["name"],
            "amount": investment_data.amount,
            "units": units
        }
    )
    db.add(activity)
    db.commit()
    
    return {
        "success": True,
        "message": f"Investment in {asset['name']} successful",
        "data": {
            "investment": UserInvestment(
                id=investment.id,
                user=investment.user_id,
                asset_id=investment.asset_id,
                asset_name=investment.asset_name,
                invested_amount=investment.invested_amount,
                current_value=investment.current_value,
                units=investment.units,
                entry_price=investment.entry_price,
                current_price=investment.current_price,
                profit_loss=investment.profit_loss,
                profit_loss_percentage=investment.profit_loss_percentage,
                status=investment.status,
                created_at=investment.created_at.isoformat(),
                completion_time=investment.completion_time.isoformat() if investment.completion_time else None
            ),
            "new_balance": wallet.balance
        }
    }

