"""
Модель пользователя
"""
from sqlalchemy import Column, String, Boolean, DateTime, func
from .base import BaseModel


class User(BaseModel):
    """Модель пользователя"""
    __tablename__ = "users"
    
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)  # admin, manager, warehouse, user
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"