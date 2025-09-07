"""
Pydantic схемы для товаров
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class ProductBase(BaseModel):
    """Базовая схема товара"""
    name: str
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    quantity: int = 0
    min_stock: int = 0
    buy_price_eur: Optional[Decimal] = None
    sell_price_rub: Optional[Decimal] = None
    supplier_name: Optional[str] = None
    availability_status: str = "IN_STOCK"
    expected_date: Optional[date] = None
    photo_path: Optional[str] = None


class ProductCreate(ProductBase):
    """Схема создания товара"""
    pass


class ProductUpdate(BaseModel):
    """Схема обновления товара"""
    name: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    quantity: Optional[int] = None
    min_stock: Optional[int] = None
    buy_price_eur: Optional[Decimal] = None
    sell_price_rub: Optional[Decimal] = None
    supplier_name: Optional[str] = None
    availability_status: Optional[str] = None
    expected_date: Optional[date] = None
    photo_path: Optional[str] = None


class ProductInDB(ProductBase):
    """Схема товара в БД"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Product(ProductBase):
    """Схема товара для API"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Схема списка товаров"""
    products: list[Product]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool