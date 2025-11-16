from pydantic import BaseModel
from datetime import datetime

class WalletBase(BaseModel):
    balance: float = 0.0
    equity: float = 0.0
    currency: str = "KES"

class WalletResponse(WalletBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DepositRequest(BaseModel):
    amount: float

class TransactionResponse(BaseModel):
    success: bool
    message: str
    new_balance: float
    new_equity: float