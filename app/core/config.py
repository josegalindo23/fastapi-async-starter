"""
app/core/config.py

Centralized application configuration using Pydantic's BaseSettings.
- Loads from environment variables and .env file
- Provides type validation and defaults for all config values
- Cached for efficient access across the app
"""
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "FastAPI Async Starter"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
 
    # Security 
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 15

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    model_config = ConfigDict(env_file=".env", case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()