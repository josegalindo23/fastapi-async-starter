"""
test/test_users.py

Tests for user registration and management endpoints.
"""

import pytest
from httpx import AsyncClient


# Registration 

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Valid registration should return 201 with user data."""
    response = await client.post("/users/register", json={
        "email": "newuser@example.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert data["role"] == "user"
    assert data["is_active"] is True
    # Password must never be returned
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, registered_user: dict):
    """Registering with an existing email should return 409."""
    response = await client.post("/users/register", json={
        "email": registered_user["email"],  # same email
        "username": "differentusername",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, registered_user: dict):
    """Registering with an existing username should return 409."""
    response = await client.post("/users/register", json={
        "email": "different@example.com",
        "username": registered_user["username"],  # same username
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password_no_uppercase(client: AsyncClient):
    """Password without uppercase should be rejected with 422."""
    response = await client.post("/users/register", json={
        "email": "weak@example.com",
        "username": "weakuser",
        "password": "nouppercase1",
        "confirm_password": "nouppercase1",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password_no_digit(client: AsyncClient):
    """Password without a digit should be rejected with 422."""
    response = await client.post("/users/register", json={
        "email": "weak2@example.com",
        "username": "weakuser2",
        "password": "NoDigitPass",
        "confirm_password": "NoDigitPass",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_passwords_dont_match(client: AsyncClient):
    """Mismatched passwords should be rejected with 422."""
    response = await client.post("/users/register", json={
        "email": "mismatch@example.com",
        "username": "mismatchuser",
        "password": "StrongPass1",
        "confirm_password": "DifferentPass1",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Invalid email format should be rejected with 422."""
    response = await client.post("/users/register", json={
        "email": "not-an-email",
        "username": "someuser",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    })
    assert response.status_code == 422


# Protected routes 

@pytest.mark.asyncio
async def test_list_users_requires_auth(client: AsyncClient):
    """GET /users/ without token should return 401."""
    response = await client.get("/users/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_requires_admin(client: AsyncClient, auth_headers: dict):
    """GET /users/ with a regular user token should return 403."""
    response = await client.get("/users/", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_profile_requires_auth(client: AsyncClient):
    """PUT /users/me/profile without token should return 401."""
    response = await client.put("/users/me/profile", json={"full_name": "New Name"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile_success(client: AsyncClient, auth_headers: dict):
    """Authenticated user should be able to update their profile."""
    response = await client.put(
        "/users/me/profile",
        json={"full_name": "Updated Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"