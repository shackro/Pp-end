from typing import Optional
from pydantic import BaseModel

class WalletData(BaseModel):
    id: int
    user_id: int
    balance: float
    equity: float
    currency: str
    created_at: str
    updated_at: str

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
    transaction_id: Optional[str] = None
