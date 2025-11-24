# app/models/transaction.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # deposit, withdrawal, investment, bonus
    amount = Column(Float)
    description = Column(String)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    status = Column(String, default="completed")
    currency = Column(String, default="KES")

class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(String, nullable=True)
    asset_name = Column(String, nullable=True)
    invested_amount = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    units = Column(Float, default=0.0)
    entry_price = Column(Float, default=0.0)
    current_price = Column(Float, default=0.0)
    profit_loss = Column(Float, default=0.0)
    profit_loss_percentage = Column(Float, default=0.0)
    status = Column(String, default="active")  # active, closed
    created_at = Column(DateTime(timezone=True), default=func.now())
    completion_time = Column(DateTime(timezone=True), nullable=True)
