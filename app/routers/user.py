"""
app/routers/users.py

User management endpoints — updated for Phase 2 with protected routes.

Public endpoints (no auth required):
    POST /users/register       - Create new account

Protected endpoints (active user required):
    GET  /users/me             - Alias → redirects to /auth/me
    PUT  /users/me/profile     - Update username, full_name
    PUT  /users/me/password    - Change password

Admin-only endpoints:
    GET  /users/               - List all users
    GET  /users/{id}           - Get any user by ID
    PUT  /users/{id}           - Admin update any user
    DELETE /users/{id}         - Deactivate user
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.db.database import get_db
from app.dependencies.auth import ActiveUser, AdminUser
from app.schemas.user import (
    UserCreate,
    UserCreateResponse,
    UserPrivate,
    UserAdminView,
    UserAdminList,
    UserProfileUpdate,
    UserPasswordUpdate,
    UserAdminUpdate,
    UserRole,
    UserUpdateResponse,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

DB = Annotated[AsyncSession, Depends(get_db)]


# ─────────────────────────────────────────────
# Public: Registration
# ─────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register_user(user_in: UserCreate, db: DB) -> UserCreateResponse:
    """
    Create a new user account.

    - Email and username must be unique
    - Password is hashed before storage (never stored in plain text)
    - New accounts get `role=user` and `is_active=True` by default
    """
    # Check uniqueness
    if await user_service.get_user_by_email(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    if await user_service.get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken",
        )

    user = await user_service.create_user(db, user_in, role=UserRole.USER)
    return UserCreateResponse.model_validate(user)


# ─────────────────────────────────────────────
# Protected: Own profile management
# ─────────────────────────────────────────────

@router.put(
    "/me/profile",
    response_model=UserUpdateResponse,
    summary="Update your profile (username, full name)",
)
async def update_my_profile(
    updates: UserProfileUpdate,
    current_user: ActiveUser,
    db: DB,
) -> UserUpdateResponse:
    """Update non-sensitive profile fields for the authenticated user."""
    # Check username uniqueness if being changed
    if updates.username and updates.username != current_user.username:
        if await user_service.get_user_by_username(db, updates.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken",
            )

    updated = await user_service.update_user(db, current_user.id, updates)
    return UserUpdateResponse.model_validate(updated)


@router.put(
    "/me/password",
    response_model=dict,
    summary="Change your password",
)
async def change_my_password(
    body: UserPasswordUpdate,
    current_user: ActiveUser,
    db: DB,
) -> dict:
    """
    Change the authenticated user's password.

    Requires the current password for verification.
    """
    success = await user_service.change_password(db, current_user, body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    return {"message": "Password changed successfully"}


# ─────────────────────────────────────────────
# Admin: User management
# ─────────────────────────────────────────────

@router.get(
    "/",
    response_model=UserAdminList,
    summary="[Admin] List all users",
)
async def list_users(
    current_user: AdminUser,
    db: DB,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> UserAdminList:
    """Paginated list of all users. Admin only."""
    skip = (page - 1) * page_size
    users, total = await user_service.get_all_users_paginated(db, skip=skip, limit=page_size)

    return UserAdminList.create(
        items=[UserAdminView.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserAdminView,
    summary="[Admin] Get user by ID",
)
async def get_user_by_id(user_id: int, current_user: AdminUser, db: DB) -> UserAdminView:
    """Fetch full details for any user by their ID. Admin only."""
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserAdminView.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserAdminView,
    summary="[Admin] Update any user",
)
async def admin_update_user(
    user_id: int,
    updates: UserAdminUpdate,
    current_user: AdminUser,
    db: DB,
) -> UserAdminView:
    """Update any field on any user. Admin only."""
    user = await user_service.admin_update_user(db, user_id, updates)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserAdminView.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Deactivate a user",
)
async def deactivate_user(user_id: int, current_user: AdminUser, db: DB) -> None:
    """
    Soft-delete: sets `is_active=False` rather than deleting from DB.
    This preserves audit trails and referential integrity.
    """
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await user_service.deactivate_user(db, user_id)