"""
app/routers/auth.py

Authentication endpoints:
    POST /auth/login          - Get access + refresh tokens
    POST /auth/refresh        - Rotate refresh token, get new access token
    POST /auth/logout         - Revoke current session's refresh token
    POST /auth/logout-all     - Revoke all sessions (all devices)
    POST /auth/password-reset/request  - Trigger reset email
    POST /auth/password-reset/confirm  - Set new password with reset token
    GET  /auth/me             - Get current authenticated user's profile
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.db.database import get_db
from app.dependencies.auth import ActiveUser
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
)
from app.schemas.user import UserPrivate
from app.services import auth_service
from app.services.auth_service import AuthenticationError, TokenError, PasswordResetError

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Type alias for DB dependency
DB = Annotated[AsyncSession, Depends(get_db)]

# Login
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    responses={
        401: {"description": "Incorrect credentials or inactive account"},
    },
)
async def login(credentials: LoginRequest, db: DB) -> TokenResponse:
    """
    Authenticate with email + password.

    Returns a short-lived **access token** and a long-lived **refresh token**.

    - Access token: include in `Authorization: Bearer <token>` header
    - Refresh token: use at `/auth/refresh` to get a new access token
    """
    try:
        return await auth_service.login(db, credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

# Refresh Token
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses={
        401: {"description": "Invalid, expired, or already-used refresh token"},
    },
)
async def refresh_token(body: RefreshTokenRequest, db: DB) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    **Token rotation** is applied: the submitted refresh token is immediately
    revoked and a new one is issued. Do not reuse old refresh tokens.
    """
    try:
        return await auth_service.refresh_access_token(db, body.refresh_token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

# Logout
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout from current session",
)
async def logout(
    body: LogoutRequest,
    current_user: ActiveUser,
    db: DB,
) -> MessageResponse:
    """
    Revoke the provided refresh token to invalidate the current session.

    The access token will remain technically valid until it expires naturally
    (since JWTs are stateless), but the refresh token can no longer be used.
    """
    await auth_service.logout(db, current_user, body.refresh_token)
    return MessageResponse(message="Successfully logged out")

@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout from all devices",
)
async def logout_all(current_user: ActiveUser, db: DB) -> MessageResponse:
    """
    Revoke **all** refresh tokens for the authenticated user.

    Use this when a user suspects their account has been compromised,
    or when implementing a "logout everywhere" feature.
    """
    revoked = await auth_service.logout_all_sessions(db, current_user)
    return MessageResponse(
        message=f"Successfully logged out from all sessions ({revoked} token(s) revoked)"
    )

# Current User Profile
@router.get(
    "/me",
    response_model=UserPrivate,
    summary="Get current user's profile",
)
async def get_me(current_user: ActiveUser) -> UserPrivate:
    """
    Return the authenticated user's own profile data.

    Requires a valid Bearer access token.
    """
    return current_user

# Password Reset
@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    summary="Request a password reset email",
)
async def request_password_reset(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: DB,
) -> MessageResponse:
    """
    Trigger a password reset for the given email.

    **Always returns 200** — even if the email doesn't exist in the system.
    This prevents user enumeration attacks.

    In production: the reset token should be emailed to the user, not returned
    in the response. The token is currently logged/printed for development only.
    """
    token = await auth_service.request_password_reset(db, body.email)

    if token:
        # TODO (Phase 4): Replace with actual email sending via background task
        # background_tasks.add_task(send_reset_email, email=body.email, token=token)
        #
        # For development — log the token so you can test without email setup
        print(f"\n[DEV ONLY] Password reset token for {body.email}:\n{token}\n")

    # Always return the same response regardless of whether email was found
    return MessageResponse(
        message="If that email is registered, you will receive a reset link shortly"
    )

@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    summary="Confirm password reset with token",
    responses={
        400: {"description": "Invalid token or passwords don't match"},
    },
)
async def confirm_password_reset(body: PasswordResetConfirm, db: DB) -> MessageResponse:
    """
    Set a new password using the token from the reset email.

    - Token is single-use and expires after `PASSWORD_RESET_TOKEN_EXPIRE_HOURS`
    - All existing sessions are revoked after a successful reset
    """
    try:
        await auth_service.confirm_password_reset(db, body)
    except PasswordResetError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MessageResponse(
        message="Password updated successfully. Please log in with your new password."
    )