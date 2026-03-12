"""
app/services/auth_service.py

Authentication business logic:
- Login (authenticate + issue tokens)
- Token refresh with rotation
- Logout (single session / all sessions)
- Password reset flow
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_token,
    TokenDecodeError,
)
from app.models.user import User
from app.models.tokens import RefreshToken
from app.schemas.auth import LoginRequest, TokenResponse, PasswordResetConfirm

# Exceptions (domain-specific, caught in router)
class AuthenticationError(Exception):
    """Wrong credentials or inactive account."""
    pass

class TokenError(Exception):
    """Invalid, expired, or revoked token."""
    pass

class PasswordResetError(Exception):
    """Password reset token invalid or passwords mismatch."""
    pass

# Internal Helpers
def _build_token_response(user: User, refresh_token_str: str) -> TokenResponse:
    """Create access + refresh token pair and wrap in response schema."""
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "email": user.email},
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

async def _store_refresh_token(db: AsyncSession, user: User, raw_token: str) -> RefreshToken:
    """
    Decode the refresh token to extract jti + expiry, then persist to DB.
    Storing in DB enables revocation and per-device logout.
    """
    payload = decode_token(raw_token, "refresh")
    jti = payload["jti"]
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    db_token = RefreshToken(
        token=raw_token,
        jti=jti,
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.flush()  # Get ID without committing — caller commits
    return db_token

# Login
async def login(db: AsyncSession, credentials: LoginRequest) -> TokenResponse:
    """
    Authenticate user with email + password, issue token pair.

    Security notes:
    - Uses constant-time comparison via passlib (prevents timing attacks)
    - Returns identical error for bad email vs bad password (prevents enumeration)
    """
    # 1. Find user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user: User | None = result.scalar_one_or_none()

    # 2. Verify — always run verify_password even if user not found
    #    to prevent timing-based email enumeration
    dummy_hash = "$2b$12$dummyhashfordummycheckthatwillalwaysfail"
    password_ok = verify_password(
        credentials.password,
        user.hashed_password if user else dummy_hash,
    )

    if not user or not password_ok:
        raise AuthenticationError("Incorrect email or password")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated. Contact support.")

    # 3. Issue tokens
    raw_refresh = create_refresh_token(user.id)
    await _store_refresh_token(db, user, raw_refresh)
    await db.commit()

    return _build_token_response(user, raw_refresh)

# Token Refresh (with rotation)
async def refresh_access_token(db: AsyncSession, raw_refresh_token: str) -> TokenResponse:
    """
    Validate the refresh token, revoke it, issue a fresh pair.

    Refresh token rotation:
    - Old refresh token is immediately revoked on use
    - New refresh token is issued alongside new access token
    - Prevents replay attacks if a token is stolen
    """
    # 1. Decode JWT
    try:
        payload = decode_token(raw_refresh_token, "refresh")
    except TokenDecodeError as e:
        raise TokenError(str(e)) from e

    jti = payload.get("jti")
    user_id = int(payload["sub"])

    # 2. Look up the token record
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.jti == jti)
    )
    db_token: RefreshToken | None = result.scalar_one_or_none()

    if not db_token or not db_token.is_valid:
        raise TokenError("Refresh token is invalid or has been revoked")

    # 3. Revoke the used token (rotation)
    db_token.revoke()

    # 4. Load user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        await db.commit()  # Persist revocation even on failure
        raise TokenError("User not found or account deactivated")

    # 5. Issue new pair
    new_raw_refresh = create_refresh_token(user.id)
    await _store_refresh_token(db, user, new_raw_refresh)
    await db.commit()

    return _build_token_response(user, new_raw_refresh)

# Logout
async def logout(db: AsyncSession, user: User, raw_refresh_token: str | None) -> None:
    """
    Revoke a single refresh token (logout from current device).

    If no refresh token provided, nothing to revoke — access token
    expiry handles session termination naturally.
    """
    if not raw_refresh_token:
        return

    try:
        payload = decode_token(raw_refresh_token, "refresh")
        jti = payload.get("jti")
    except TokenDecodeError:
        return  # Token already invalid — treat as already logged out

    result = await db.execute(
        select(RefreshToken).where(
            and_(RefreshToken.jti == jti, RefreshToken.user_id == user.id)
        )
    )
    db_token = result.scalar_one_or_none()
    if db_token and not db_token.is_revoked:
        db_token.revoke()
        await db.commit()

async def logout_all_sessions(db: AsyncSession, user: User) -> int:
    """
    Revoke all active refresh tokens for a user (logout from all devices).

    Returns:
        Number of tokens revoked
    """
    result = await db.execute(
        select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
    )
    tokens = result.scalars().all()

    revoked_count = 0
    for token in tokens:
        if token.is_valid:
            token.revoke()
            revoked_count += 1

    await db.commit()
    return revoked_count

# Password Reset
async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """
    Generate a password reset token for the given email.

    Returns:
        The reset token string (caller sends this via email),
        or None if no user found (caller should NOT expose this difference).

    Security: always return 200 to the client regardless of whether
    the email exists — prevents user enumeration.
    """
    result = await db.execute(select(User).where(User.email == email))
    user: User | None = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None  # Silently fail

    return create_password_reset_token(user.id)

async def confirm_password_reset(db: AsyncSession, data: PasswordResetConfirm) -> None:
    """
    Validate reset token and set a new password.

    Raises:
        PasswordResetError: on any validation failure
    """
    # 1. Validate passwords match
    if not data.validate_passwords_match():
        raise PasswordResetError("Passwords do not match")

    # 2. Decode token
    try:
        payload = decode_token(data.token, "password_reset")
        user_id = int(payload["sub"])
    except (TokenDecodeError, ValueError) as e:
        raise PasswordResetError("Reset token is invalid or has expired") from e

    # 3. Load user
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise PasswordResetError("Reset token is invalid or has expired")

    # 4. Update password
    user.hashed_password = get_password_hash(data.new_password)

    # 5. Revoke all refresh tokens (force re-login everywhere after reset)
    await logout_all_sessions(db, user)

    await db.commit()