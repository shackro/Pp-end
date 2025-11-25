# app/schemas/wallet.py
from pydantic import BaseModel
from datetime import datetime

class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: float
    equity: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True  # Updated for Pydantic V2

class DepositRequest(BaseModel):
    amount: float
    phone_number: str

class WithdrawRequest(BaseModel):
    amount: float
    phone_number: str

class TransactionResponse(BaseModel):
    success: bool
    message: str
    new_balance: float
    new_equity: float

# Add this for PnL data
class PnLData(BaseModel):
    profit: float
    loss: float
    net: float  # optional, can be profit - loss

    class Config:
        from_attributes = True  # Updated for Pydantic V2
