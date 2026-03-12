"""
app/services/user_service.py

User business logic:
- CRUD operations
- Password management
- Admin operations

Note: authenticate_user logic lives in auth_service.py to keep
auth concerns separated from user management concerns.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import (UserCreate, UserProfileUpdate, 
                              UserPasswordUpdate, UserRole, UserAdminUpdate)

# Create operations
async def create_user(db: AsyncSession, user_in: UserCreate, role: UserRole) -> User:
    """Create a new user with hashed password."""

    user = User(
        email =user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=role.value
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

# Read operations
async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> User| None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> User| None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_all_users(db:AsyncSession, skip: int = 0, limit: int =100) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

async def get_all_users_paginated(db: AsyncSession, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
    """Return users + total count for pagination."""
    user_result = await db.execute(select(User).offset(skip).limit(limit))
    count_result = await db.execute(select(func.count()).select_from(User))
    return list(user_result.scalars().all()), count_result.scalar_one()

# Update operations
async def update_user(db: AsyncSession, user_id: int, user_update: UserProfileUpdate) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user 

async def change_password(db: AsyncSession, user: User, 
                          body: UserPasswordUpdate) -> bool:
    """Verify current password and update to new password. Returns True if successful."""
    if not verify_password(body.current_password, user.hashed_password):
        return False  # Current password is incorrect

    user.hashed_password = get_password_hash(body.new_password)
    await db.commit()
    return True

async def admin_update_user(db: AsyncSession, user_id: int, 
                            updates: UserAdminUpdate) -> Optional[User]:
    """Admin update any user field."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    update_dict = updates.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user

# Soft delete operation
async def deactivate_user(db: AsyncSession, user_id: int) -> bool:
    """Soft-delete: set is_active=False. Preserves data and audit trails."""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.is_active = False
    await db.commit()
    return True