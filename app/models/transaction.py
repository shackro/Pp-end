# app/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.user import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # deposit, withdrawal, investment, bonus
    amount = Column(Float)
    description = Column(String)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    status = Column(String, default="completed")  # completed, pending, failed
    currency = Column(String, default="KES")

# app/models/investment.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.user import Base

class Investment(Base):
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(String)
    asset_name = Column(String)
    invested_amount = Column(Float)
    current_value = Column(Float)
    units = Column(Float)
    profit_loss = Column(Float)
    profit_loss_percentage = Column(Float)
    status = Column(String, default="active")  # active, closed
    created_at = Column(DateTime(timezone=True), default=func.now())