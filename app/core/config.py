import os
from typing import List

class Settings:
    # App
    environment: str = os.getenv("ENVIRONMENT", "development")
    secret_key: str = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaGFja3JvYXJlbEBnbWFpbC5jb20iLCJleHAiOjE3NjQwNjc3ODd9.j5xhoo0Pv1Lg9jAbrHAWPiUMnOG8b4MoTlwWaBA9FG8", "5L5vfBJhjFPBGfMtXh_m5AjPVBXNTXCcPyqlYyJTsOU")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./PesaPrime.db")
    
    # CORS
    allowed_origins: List[str] = ["pesaprime.vercel.app", "http://localhost:3000"]

settings = Settings()
