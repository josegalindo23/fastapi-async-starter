from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.database import engine
from app.db.base import Base
from app.routers.health import router as health_router
from app.routers.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    #shutdown
    await engine.dispose()

app = FastAPI(title="FastAPI Async Starter", version="1.0.0", lifespan=lifespan)

#CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(users_router)
