from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # App
    PROJECT_NAME: str = "FastAPI Async Starter"
    VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Security (for future implementation of authentication JWT, OAuth2, etc.)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()