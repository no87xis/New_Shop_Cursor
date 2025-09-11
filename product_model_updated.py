"""
Обновленная модель товара с поддержкой фото
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Product(Base):
    """Модель товара с поддержкой фото"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    detailed_description = Column(Text)
    
    # Фото товара
    photo_url = Column(String(500), default="/static/images/placeholder-product.jpg")
    photo_alt = Column(String(200), default="Изображение товара")
    
    # Количество и склад
    quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    
    # Цены
    buy_price_eur = Column(Numeric(10, 2))
    sell_price_rub = Column(Numeric(10, 2))
    
    # Поставщик
    supplier_name = Column(String(255))
    
    # Статус доступности
    availability_status = Column(String(50), default="IN_STOCK")
    expected_date = Column(DateTime)
    
    # Временные метки
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Дополнительные поля для фото
    has_photo = Column(Boolean, default=False)
    photo_uploaded_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', has_photo={self.has_photo})>"
    
    def to_dict(self):
        """Преобразует объект в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "detailed_description": self.detailed_description,
            "photo_url": self.photo_url,
            "photo_alt": self.photo_alt,
            "quantity": self.quantity,
            "min_stock": self.min_stock,
            "buy_price_eur": float(self.buy_price_eur) if self.buy_price_eur else None,
            "sell_price_rub": float(self.sell_price_rub) if self.sell_price_rub else None,
            "supplier_name": self.supplier_name,
            "availability_status": self.availability_status,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "has_photo": self.has_photo,
            "photo_uploaded_at": self.photo_uploaded_at.isoformat() if self.photo_uploaded_at else None
        }
    
    def get_photo_url(self) -> str:
        """Возвращает URL фото или placeholder"""
        if self.photo_url and self.photo_url != "/static/images/placeholder-product.jpg":
            return self.photo_url
        return "/static/images/placeholder-product.jpg"
    
    def get_thumbnail_url(self) -> str:
        """Возвращает URL миниатюры"""
        if self.photo_url and self.photo_url != "/static/images/placeholder-product.jpg":
            # Заменяем путь на миниатюру
            base_url = self.photo_url.replace("/static/uploads/products/", "/static/uploads/products/thumbnails/")
            return base_url
        return "/static/images/placeholder-product.jpg"
    
    def update_photo(self, photo_url: str, photo_alt: str = None):
        """Обновляет фото товара"""
        self.photo_url = photo_url
        self.photo_alt = photo_alt or "Изображение товара"
        self.has_photo = photo_url != "/static/images/placeholder-product.jpg"
        self.photo_uploaded_at = datetime.now()
        self.updated_at = datetime.now()