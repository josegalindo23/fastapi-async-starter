"""
app/core/security.py

Centralized security utilities:
- Password hashing and verification (bcrypt via passlib)
- JWT access and refresh token creation/decoding
- Password validation configurations (used by schemas)
"""

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
import secrets

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordValidationConfig:
    """Centralized password policy configuration."""
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False  # Configurable based on security needs

# Password 
def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

# Token Types
TokenType = Literal["access", "refresh", "password_reset"]

#JWT Token Creation 
def create_access_token(subject: str|int, extra_claims: dict|None = None) -> str:
    """Create a short-lived JWT access token.
     - `subject`: Unique identifier for the token (e.g., user ID or email)
     - `extra_claims`: Optional additional claims to include in the token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(subject), "exp": expire, "iat": now, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str|int) -> str:
    """Create a long-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(subject), "exp": expire, "iat": now, "type": "refresh", 
               "jti": secrets.token_hex(16)}  
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_password_reset_token(subject: str|int) -> str:
    """Create a short-lived password reset token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(subject), "exp": expire, "iat": now, "type": "password_reset",
               "jti": secrets.token_hex(16)}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

#JWT Token Decoding / Verification

class TokenDecodeError(Exception):
    """Raised when a JWT cannot be decoded or is invalid."""
    pass

def decode_token(token: str, expected_type: TokenType) -> dict:
    """Verify a JWT token and return the decoded payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise TokenDecodeError(f"Token validation failed:{e}") from e
    
    #Enforce token type - prevents refresh tokens being used as access tokens
    token_type = payload.get("type")
    if token_type != expected_type:
        raise TokenDecodeError(f"Invalid token type: expected {expected_type}, got {token_type}")
    return payload

def get_user_id_from_token(token: str, expected_type: TokenType) -> int:
    """Convenience wrapper: decode token and return the user ID as int"""
    payload = decode_token(token, expected_type)
    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as e:
        raise TokenDecodeError(f"Invalid 'sub' claim: {e}") from e