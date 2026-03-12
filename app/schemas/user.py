from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, TypeVar, Generic
from enum import Enum

from app.core.security import PasswordValidationConfig

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

# Base User Schema
class UserBase(BaseModel):
    """Base user attributes shared across schemas."""
    email: EmailStr = Field(..., description="Valid email address", example=["user@example.com"], json_schema_extra={"format": "email"})
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="Username (letters, numbers, underscores)", examples=["john_doe", "user123"])
    full_name: Optional[str] = Field(None, max_length=100, description="User's Full Name", examples=["John Doe", "Jane Smith"])

# Input schema (client -> API) - Registration and Authentication
class UserCreate(UserBase):
    """Schema for user registration."""
    password : str = Field(..., min_length=PasswordValidationConfig.MIN_LENGTH, max_length=PasswordValidationConfig.MAX_LENGTH,
                            description="Password (min 8 characters)", examples=["strongpassword123", "P@ssw0rd!"])
    confirm_password : str = Field(..., description="Confirm Password", examples=["strongpassword123", "P@ssw0rd!"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if PasswordValidationConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if PasswordValidationConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if PasswordValidationConfig.REQUIRE_DIGIT and not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        # Optional: special characters
        if PasswordValidationConfig.REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?`~" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v
    
    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        """Ensure password and confirm_password match."""
        if self.password != self.confirm_password:
            raise ValueError("Password and Confirm Password do not match")
        return self

# Profile Update Inputs
class UserProfileUpdate(BaseModel):
    """Update non-sensitive profile information."""
    username:  Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", 
                                     description="New username (letters, numbers, underscores)", examples=["new_username", "user456"])
    full_name: Optional[str] = Field(None, max_length=100, description="User's Full Name", examples=["New Full Name", "Another Name"])
    
class UserEmailUpdate(BaseModel):
    """Update email address"""
    email: Optional[EmailStr] = Field(None, description="Valid email address", example=["new_email@example.com"])
    current_password: Optional[str] = Field(None, description="Current Password", examples=["currentpassword123"])

class UserPasswordUpdate(BaseModel):
    """Update password with security verification"""
    current_password: str = Field(..., description="Current Password", examples=["currentpassword123"])
    new_password: Optional[str] = Field(None, min_length=PasswordValidationConfig.MIN_LENGTH, max_length=PasswordValidationConfig.MAX_LENGTH,
                                         description="New Password (min 8 characters)", examples=["newstrongpassword", "N3wP@ssw0rd!"])
    confirm_new_password: Optional[str] = Field(None, description="Confirm New Password", examples=["newstrongpassword", "N3wP@ssw0rd!"])

    @model_validator(mode="after")
    def validate_password_change(self) -> "UserPasswordUpdate":
        """Ensure new password and confirmation match."""
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self
    
# Administrative schema (for admin endpoints only)
class UserAdminCreate(UserCreate):
    """Admin-only: Create user with specified role and status"""
    role: UserRole = Field(UserRole.USER, description="Role assigned to the user")
    is_active: bool = Field(True, description="Account active status (admin only)")
    is_superuser: bool = Field(False, description="Superuser status (admin only)")

class UserAdminUpdate(BaseModel):
    """Admin-only: Update any user field"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

# Database Schemas (Internal use only)
class UserInDB(UserBase):
    """
    Schema representing how the user is stored in the database.
    Includes sensitive fields and MUST NOT be returned to clients.
    """
    id: int
    hashed_password: str
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Output schema (API -> client)

class UserPublic(UserBase):
    """Public-facing user schema (what other users see)"""
    id: int
    # Note: No role, no status, no dates - minimal public info
    # created_at: datetime  # Optional: might omit for privacy

    model_config = ConfigDict(from_attributes=True)

class UserPrivate(UserBase):
    """Private user schema (what the user themselves sees)"""
    id: int
    email: EmailStr # User can see their own email, redundant but explicit
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  

class UserAdminView(UserBase):
    """Admin-facing user schema (full details)"""
    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Compatibility and Generic Schemas

# For backward compatibility and general use
UserRead = UserPrivate  # Alias for UserPrivate


T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response for any resource."""
    items: List[T]
    total: int
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool
    has_previous: bool

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Factory method to create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )


class UserList(PaginatedResponse[UserPublic]):
    """Paginated list of public users."""
    pass


class UserAdminList(PaginatedResponse[UserAdminView]):
    """Paginated list of users for admin view."""
    pass

# Response Schemas

class UserCreateResponse(UserPrivate):
    """Response after successful user creation."""
    message: str = Field("User created successfully", description="Success message")


class UserUpdateResponse(UserPrivate):
    """Response after successful user update."""
    message: str = Field("User updated successfully", description="Success message")

# Statistical and Summary Schemas

class UserStats(BaseModel):
    """User statistics for dashboards."""
    total_users: int
    active_users: int
    admin_users: int
    moderator_users: int
    registered_today: int
    registered_last_7_days: int
    registered_last_30_days: int


class UserSummary(BaseModel):
    """Brief user summary for listings."""
    id: int
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)