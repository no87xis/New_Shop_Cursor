from sqlalchemy import Column, String, Integer, Float, Date, Text
from app.models.base import BaseModel

class Product(BaseModel):
    __tablename__ = "products"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    buy_price_eur = Column(Float)
    sell_price_rub = Column(Float, nullable=False)
    supplier_name = Column(String(255))
    availability_status = Column(String(50), default="IN_STOCK")
    expected_date = Column(Date)
    photo_path = Column(String(500))