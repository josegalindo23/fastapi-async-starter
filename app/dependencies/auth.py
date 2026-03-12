"""
app/dependencies/auth.py

FastAPI dependencies for authentication and authorization.
Usage in routes:
    @router.get("/me")
    async def get_me(current_user: CurrentUser):
        return current_user
    @router.delete("/admin/users/{id}")
    async def delete_user(current_user: AdminUser):
        ...
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_user_id_from_token, TokenDecodeError
from app.db.database import get_db
from app.models.user import User

# Bearer token extractor 

bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTIONS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# Core dependency
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Extract and validate the Bearer token from the Authorization header.
    Return the authenticated User ORM object.
    Raises 401 if:
    - No token provided
    - Token is invalid or expired
    - User not found in db
    """
    if credentials is None:
        raise CREDENTIALS_EXCEPTIONS
    token = credentials.credentials
    try:
        user_id = get_user_id_from_token(token, expected_type="access")
    except TokenDecodeError:
        raise CREDENTIALS_EXCEPTIONS
    
    result = await db.execute(select(User).where(User.id == user_id))
    user : User|None = result.scalar_one_or_none()
    
    if user is None:
        raise CREDENTIALS_EXCEPTIONS
    
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Extends get_current_user - also verifies the account is active.
    Use this for any endpoint that should reject desactivated accounts.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return current_user

async def get_current_admin_user(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Extends get_current_active_user - also verifies admin/superuser role.
    Use this for admin-only endpoint.
    """
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user

# Type aliases for clean router signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]