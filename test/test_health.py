"""
test/test_health.py

Tests for the health check endpoint.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(client: AsyncClient):
    """Health endpoint should always return 200."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check_response_body(client: AsyncClient):
    """Health endpoint should return expected fields."""
    response = await client.get("/health")
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Root endpoint should return docs links."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
    assert "redoc" in data