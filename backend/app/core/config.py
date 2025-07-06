from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator
from typing import List, Optional, Union
from pathlib import Path
import os

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Janawar API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Frontend URL
        "http://localhost:8000",  # Backend URL
    ]

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "janawar"
    POSTGRES_PASSWORD: str = "janawar123"
    POSTGRES_DB: str = "janawar"
    DATABASE_URI: Optional[str] = None

    # File storage
    AUDIO_UPLOAD_DIR: str = str(Path(__file__).parent.parent.parent / "data" / "audio")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_TYPES = ["audio/wav", "audio/mpeg", "audio/ogg"]

    # BirdNET settings
    BIRDNET_MODEL_PATH: str = str(Path(__file__).parent.parent.parent / "birdnet" / "model")
    BIRDNET_LABELS_PATH: str = str(Path(__file__).parent.parent.parent / "birdnet" / "labels.csv")
    BIRDNET_MIN_CONFIDENCE: float = 0.7

    # GPS settings
    DEFAULT_LATITUDE: float = 34.4167  # Default to Wular Lake
    DEFAULT_LONGITUDE: float = 74.5833

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"

    class Config:
        case_sensitive = True
        env_file = ".env"

# Create instance of settings
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
