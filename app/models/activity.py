from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base  # Make sure you have your SQLAlchemy Base

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)  # Type of activity, e.g., "login", "purchase"
    user_id = Column(Integer, nullable=True)  # Optional user reference
    data = Column(JSON, nullable=True)  # Flexible JSON to store any extra info
    created_at = Column(DateTime(timezone=True), server_default=func.now())
