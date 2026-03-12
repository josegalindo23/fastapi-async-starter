"""
app/db/base.py

Base class for SQLAlchemy ORM models.
- All ORM models should inherit from this Base class.
- This file also imports all models to register them with the Base's metadata.
- This is important for Alembic migrations and other operations that rely on the metadata.
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from app.models.user import User # noqa: F401
from app.models.tokens import RefreshToken # noqa: F401