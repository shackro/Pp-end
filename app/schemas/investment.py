# app/schemas/investment.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InvestmentCreate(BaseModel):
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    amount: float

class InvestmentResponse(BaseModel):
    id: int
    user_id: int
    asset_id: Optional[str]
    asset_name: Optional[str]
    invested_amount: float
    current_value: float
    units: float
    profit_loss: float
    profit_loss_percentage: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
