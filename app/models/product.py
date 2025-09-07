"""
Модель товара
"""
from sqlalchemy import Column, String, Text, Integer, Numeric, Date, DateTime, func
from .base import BaseModel


class Product(BaseModel):
    """Модель товара"""
    __tablename__ = "products"
    
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    detailed_description = Column(Text)
    quantity = Column(Integer, default=0, nullable=False)  # общий приход
    min_stock = Column(Integer, default=0, nullable=False)  # порог низкого остатка
    buy_price_eur = Column(Numeric(10, 2))  # входная цена в евро
    sell_price_rub = Column(Numeric(10, 2))  # розничная цена в рублях
    supplier_name = Column(String)
    availability_status = Column(String(20), default="IN_STOCK", nullable=False)  # IN_STOCK, ON_ORDER, IN_TRANSIT
    expected_date = Column(Date)  # дата ожидаемого поступления
    photo_path = Column(String)  # путь к фото товара
    
    def __repr__(self):
        return f"<Product(name='{self.name}', quantity={self.quantity}, status='{self.availability_status}')>"