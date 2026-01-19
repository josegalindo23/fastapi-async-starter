from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.models.users import User
from app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:

    # Hash the password before storing
    hashed_password = pwd_context.hash(user_in.password)

    user = User(
        email =user_in.email,
        username=user_in.username,
        hashed_password=hashed_password 
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> User| None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_all_users(db:AsyncSession, skip: int = 0, limit: int =100) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify a password against its hash
    return pwd_context.verify(plain_password, hashed_password)