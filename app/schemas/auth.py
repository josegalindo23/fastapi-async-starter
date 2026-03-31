"""
app/schemas/auth.py

Pydantic schemas for authentication flows:
- Login request/response
- Token payloads
- Refresh token request
- Password reset request/confirm
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Login
class LoginRequest(BaseModel):
    """Credentials submitted by the user to log in."""
    email: EmailStr = Field(..., description="Registered email address", examples=["user@example.com"])
    password: str = Field(..., min_length=1, description="Account password", examples=["StrongPass1"])

# Token Responses
class TokenResponse(BaseModel):
    """
    Returned after successful login or token refresh.

    - access_token: short-lived, sent in Authorization header
    - refresh_token: long-lived, used only at /auth/refresh
    - token_type: always "bearer" per OAuth2 spec
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")

class AccessTokenResponse(BaseModel):
    """Returned when only a new access token is issued (e.g. silent refresh)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Refresh
class RefreshTokenRequest(BaseModel):
    """Sent by the client to get a new access token."""
    refresh_token: str = Field(..., description="Valid refresh token previously issued by the server")


# Logout
class LogoutRequest(BaseModel):
    """Optionally send the refresh token to revoke it on logout."""
    refresh_token: str | None = Field(
        None,
        description="Refresh token to revoke. If omitted, only the current session is ended."
    )

class LogoutAllRequest(BaseModel):
    """Revoke all refresh tokens for the authenticated user."""
    pass  # No body needed — identity comes from access token

# Password Reset
class PasswordResetRequest(BaseModel):
    """
    Step 1: User provides their email to receive a reset link.
    Always returns 200 to prevent email enumeration attacks.
    """
    email: EmailStr = Field(..., description="Email address associated with the account")

class PasswordResetConfirm(BaseModel):
    """Step 2: User submits the reset token + new password."""
    token: str = Field(..., description="Password reset token from the email link")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars)",
        examples=["NewStrongPass1"],
    )
    confirm_password: str = Field(..., description="Must match new_password")

    def validate_passwords_match(self) -> bool:
        return self.new_password == self.confirm_password

# Generic Message Response
class MessageResponse(BaseModel):
    """Simple success/info message response."""
    message: str

    model_config = ConfigDict(json_schema_extra={"example": {"message": "Operation completed successfully"}})
