from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, get_user_by_id, get_all_users, get_user_by_email

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead, status_code=201)
async def create_user_endpoint(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, user_in)
    return user

@router.get("/{user_id}", response_model=UserRead)
async def get_user_endpoint(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=list[UserRead])
async def get_all_users_endpoint(skip = 0, limit = 100, db: AsyncSession = Depends(get_db)):
    users = await get_all_users(db, skip=skip, limit=limit)
    return users