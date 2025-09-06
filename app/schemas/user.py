"""
Pydantic схемы для пользователей
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str
    role: str = "user"
    is_active: bool = True


class UserCreate(UserBase):
    """Схема создания пользователя"""
    password: str


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""
    username: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """Схема пользователя в БД"""
    id: int
    hashed_password: str
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserBase):
    """Схема пользователя для API"""
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Схема входа пользователя"""
    username: str
    password: str