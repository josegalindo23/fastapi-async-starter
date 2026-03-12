"""
app/models/user.py

User SQLAlchemy model.
- Represents users in the system with fields for authentication, profile, and role management.
- Has a relationship to RefreshToken for managing issued refresh tokens.
- Inherits from Base, which is the declarative base for SQLAlchemy models.
- This model is used across the app for user management, authentication, and authorization.
- The authenticate_user logic lives in auth_service.py to keep auth concerns separated from user management concerns.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.tokens import RefreshToken

class User(Base):
    __tablename__ = "users"

    # Primary Key
    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Auth fields
    email : Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username : Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password : Mapped[str] = mapped_column(String, nullable=False) 
    
    # Profile fields
    full_name : Mapped[str] = mapped_column(String, nullable=True)
    
    #Roles and Permissions
    role : Mapped[str] = mapped_column(String, nullable=False, default="user") 
    is_superuser : Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) 
    
    # Status fields
    is_active : Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified : Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), 
                                                default=lambda: datetime.now(timezone.utc), 
                                                nullable=False)
    updated_at : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), 
                                                default=lambda: datetime.now(timezone.utc), 
                                                onupdate=lambda:datetime.now(timezone.utc), 
                                                nullable=False) 

    # === Relationships ===
    # Relationship to RefreshToken (one-to-many - a user can have multiple refresh tokens)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"