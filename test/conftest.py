"""
test/conftest.py

Shared pytest fixtures for all test modules.

Architecture:
- Uses a separate in-memory SQLite DB for tests (never touches your real test.db)
- Creates tables fresh for each test session
- Provides an async HTTP client via httpx.AsyncClient
- Provides helper fixtures: registered user, auth tokens
"""


import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.base import Base
from app.db.database import get_db

# Test database (in-memory SQLite, isolated from dev DB)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Override get_db to use test DB 
async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


# Session-scoped: create tables once per test run 
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # 🔥 ESTA LÍNEA ES LA CLAVE
    await test_engine.dispose()

# Function-scoped: fresh HTTP client per test
@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# Reusable test user data 
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "StrongPass1",
    "confirm_password": "StrongPass1",
}


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a user and return the response data."""
    response = await client.post("/users/register", json=TEST_USER)
    # If user already exists (409) that's fine, return existing
    assert response.status_code in (201, 409)
    return TEST_USER


@pytest_asyncio.fixture
async def auth_tokens(client: AsyncClient, registered_user: dict) -> dict:
    """Login and return access + refresh tokens."""
    response = await client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert response.status_code == 200
    return response.json()


@pytest_asyncio.fixture
async def auth_headers(auth_tokens: dict) -> dict:
    """Return Authorization header dict for protected endpoints."""
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}