import os
from typing import List

class Settings:
    # App
    environment: str = os.getenv("ENVIRONMENT", "development")
    secret_key: str = os.getenv("SECRET_KEY", "5L5vfBJhjFPBGfMtXh_m5AjPVBXNTXCcPyqlYyJTsOU")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./PesaPrime.db")
    
    # CORS
    allowed_origins: List[str] = ["pesaprime.vercel.app", "http://localhost:3000"]

settings = Settings()
