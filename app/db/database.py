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