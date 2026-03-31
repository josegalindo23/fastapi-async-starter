"""
test/test_auth.py

Tests for all authentication endpoints:
- Login, refresh token rotation, logout, password reset
- Protected route access with valid/invalid tokens
"""

import pytest
from httpx import AsyncClient


# Login

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user: dict):
    """Valid credentials should return access + refresh tokens."""
    response = await client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800  # 30 minutes in seconds


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    """Wrong password should return 401."""
    response = await client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": "WrongPassword1",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Non-existent email should return 401 (same as wrong password)."""
    response = await client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": "StrongPass1",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_fields(client: AsyncClient):
    """Missing fields should return 422."""
    response = await client.post("/auth/login", json={"email": "test@example.com"})
    assert response.status_code == 422


# Get current user

@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient, auth_headers: dict, registered_user: dict):
    """Authenticated user should get their own profile."""
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["email"]
    assert data["username"] == registered_user["username"]
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    """Request without token should return 401."""
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Invalid token should return 401."""
    response = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer this.is.not.a.valid.token"},
    )
    assert response.status_code == 401


# Refresh token

@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, auth_tokens: dict):
    """Valid refresh token should return new token pair."""
    response = await client.post("/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"],
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New tokens should be different from the old ones (rotation)
    # assert data["access_token"] != auth_tokens["access_token"]
    # assert data["refresh_token"] != auth_tokens["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Invalid refresh token should return 401."""
    response = await client.post("/auth/refresh", json={
        "refresh_token": "invalid.token.here",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient, auth_tokens: dict):
    """Used refresh token should be revoked and rejected on reuse."""
    refresh_token = auth_tokens["refresh_token"]

    # First use, Should succeed
    response1 = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response1.status_code == 200

    # Reuse old token, should be rejected (rotation revoked it)
    response2 = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response2.status_code == 401


# Logout 

@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, auth_headers: dict, auth_tokens: dict):
    """Logout with valid refresh token should return 200."""
    response = await client.post(
        "/auth/logout",
        json={"refresh_token": auth_tokens["refresh_token"]},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_logout_invalid_refresh_token_still_200(
    client: AsyncClient, auth_headers: dict
):
    """
    Logout with an invalid refresh token should still return 200.
    Nothing to revoke = already logged out = success.
    """
    response = await client.post(
        "/auth/logout",
        json={"refresh_token": "garbage.token.value"},
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout_requires_auth(client: AsyncClient):
    """Logout without access token should return 401."""
    response = await client.post(
        "/auth/logout",
        json={"refresh_token": "anytoken"},
    )
    assert response.status_code == 401


# Password reset 

@pytest.mark.asyncio
async def test_password_reset_request_existing_email(
    client: AsyncClient, registered_user: dict
):
    """Reset request for existing email should return 200."""
    response = await client.post("/auth/password-reset/request", json={
        "email": registered_user["email"],
    })
    assert response.status_code == 200
    assert "registered" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_password_reset_request_nonexistent_email(client: AsyncClient):
    """
    Reset request for non-existent email should also return 200.
    Prevents user enumeration attacks.
    """
    response = await client.post("/auth/password-reset/request", json={
        "email": "ghost@example.com",
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_confirm_invalid_token(client: AsyncClient):
    """Invalid reset token should return 400."""
    response = await client.post("/auth/password-reset/confirm", json={
        "token": "invalid.reset.token",
        "new_password": "NewStrongPass1",
        "confirm_password": "NewStrongPass1",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_confirm_passwords_mismatch(client: AsyncClient):
    """Mismatched passwords in confirm should return 400."""
    response = await client.post("/auth/password-reset/confirm", json={
        "token": "sometoken",
        "new_password": "NewStrongPass1",
        "confirm_password": "DifferentPass1",
    })
    assert response.status_code == 400