import os
from typing import List

class Settings:
    # App
    environment: str = os.getenv("ENVIRONMENT", "development")
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./PesaPrime.db")
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:8002"]

settings = Settings()