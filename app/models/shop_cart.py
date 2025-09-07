from sqlalchemy import Column, String, Integer, Float
from app.models.base import BaseModel

class ShopCart(BaseModel):
    __tablename__ = "shop_cart"
    
    session_id = Column(String(255), nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)