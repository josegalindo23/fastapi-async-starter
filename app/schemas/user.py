from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password : str

class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 style

    # class Config:
        # from_attributes = True # Enable ORM mode to work with SQLAlchemy models: SQLAlchemy objects -> Pydantic schema

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username:  Optional[str] = None
    password: Optional[str] = None

"""
For README.md documentation:
- **Type Hints**: Code types for better clarity and error checking  
- **CORS Configuration**: Middleware setup for cross-origin requests, essential for frontend-backend communication
"""