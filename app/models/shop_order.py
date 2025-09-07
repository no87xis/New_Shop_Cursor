from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import BaseModel

class ShopOrder(BaseModel):
    __tablename__ = "shop_orders"
    
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_email = Column(String(255))
    customer_address = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="NEW")
    notes = Column(Text)
    order_date = Column(DateTime(timezone=True), server_default=func.now())