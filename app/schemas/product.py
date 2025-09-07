from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    quantity: int = 0
    min_stock: int = 0
    buy_price_eur: Optional[float] = None
    sell_price_rub: float
    supplier_name: Optional[str] = None
    availability_status: str = "IN_STOCK"
    expected_date: Optional[date] = None
    photo_path: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True