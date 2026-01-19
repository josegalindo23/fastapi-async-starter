"""
Nota:
Si no quieres perder los datos (aunque en desarrollo no importa), necesitarías usar un sistema de migraciones como Alembic. 
Pero para este proyecto, recrear la base de datos es aceptable.
"""

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False) # almacenar contraseñas hasheadas, util para autenticación
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # util para auditoría o rastreo de cambios