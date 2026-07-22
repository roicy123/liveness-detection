import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Liveness Detection API"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev_secret_only")
    algorithm: str = "HS256"
    session_timeout_seconds: int = 300 # 5 minutes

    # Redis state management
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Thresholds for Decision Fusion
    high_confidence_threshold: float = float(os.getenv("HIGH_CONFIDENCE_THRESHOLD", "0.85"))
    low_confidence_threshold: float = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.40"))

    class Config:
        env_file = ".env"

settings = Settings()
