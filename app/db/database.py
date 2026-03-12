"""
app/db/database.py

Database connection and session management using SQLAlchemy's async support.
- Creates an async engine based on the DATABASE_URL from settings
- Provides an async session factory (AsyncSessionLocal)
- Defines a dependency function `get_db` that yields an async session for use in FastAPI routes
- Ensures proper cleanup of sessions after use
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings
#from collections.abc import AsyncGenerator
from typing import AsyncGenerator

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {} # Solo para SQLite
    )

AsyncSessionLocal = async_sessionmaker(engine, class_= AsyncSession, expire_on_commit=False)

#async def get_db() -> AsyncSession[AsyncSession, None]:
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()