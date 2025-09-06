"""
Pydantic схемы для заказов
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class OrderBase(BaseModel):
    """Базовая схема заказа"""
    phone: str
    customer_name: Optional[str] = None
    client_city: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    qty: int
    unit_price_rub: Decimal
    eur_rate: Decimal = 0
    payment_method: str = "unpaid"
    payment_note: Optional[str] = None
    status: str = "paid_not_issued"
    whatsapp_phone: Optional[str] = None
    consent_whatsapp: bool = True


class OrderCreate(OrderBase):
    """Схема создания заказа"""
    pass


class OrderUpdate(BaseModel):
    """Схема обновления заказа"""
    phone: Optional[str] = None
    customer_name: Optional[str] = None
    client_city: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    qty: Optional[int] = None
    unit_price_rub: Optional[Decimal] = None
    eur_rate: Optional[Decimal] = None
    payment_method: Optional[str] = None
    payment_note: Optional[str] = None
    status: Optional[str] = None
    arrival_status: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    consent_whatsapp: Optional[bool] = None


class OrderInDB(OrderBase):
    """Схема заказа в БД"""
    id: int
    order_code: str
    order_code_last4: str
    arrival_status: str = "pending"
    arrival_notified_at: Optional[datetime] = None
    arrival_notifications_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Order(OrderBase):
    """Схема заказа для API"""
    id: int
    order_code: str
    order_code_last4: str
    arrival_status: str = "pending"
    arrival_notified_at: Optional[datetime] = None
    arrival_notifications_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShopOrderBase(BaseModel):
    """Базовая схема заказа магазина"""
    customer_name: str
    customer_phone: str
    customer_city: Optional[str] = None
    product_id: Optional[int] = None
    product_name: str
    quantity: int
    unit_price_rub: Decimal
    total_amount: Decimal
    delivery_option: Optional[str] = None
    delivery_city_other: Optional[str] = None
    delivery_cost_rub: Optional[Decimal] = None
    whatsapp_phone: Optional[str] = None
    consent_whatsapp: bool = True


class ShopOrderCreate(ShopOrderBase):
    """Схема создания заказа магазина"""
    pass


class ShopOrderUpdate(BaseModel):
    """Схема обновления заказа магазина"""
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_city: Optional[str] = None
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    unit_price_rub: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    delivery_option: Optional[str] = None
    delivery_city_other: Optional[str] = None
    delivery_cost_rub: Optional[Decimal] = None
    status: Optional[str] = None
    arrival_status: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    consent_whatsapp: Optional[bool] = None


class ShopOrderInDB(ShopOrderBase):
    """Схема заказа магазина в БД"""
    id: int
    order_code: str
    order_code_last4: str
    status: str = "ordered_not_paid"
    arrival_status: str = "pending"
    arrival_notified_at: Optional[datetime] = None
    arrival_notifications_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShopOrder(ShopOrderBase):
    """Схема заказа магазина для API"""
    id: int
    order_code: str
    order_code_last4: str
    status: str = "ordered_not_paid"
    arrival_status: str = "pending"
    arrival_notified_at: Optional[datetime] = None
    arrival_notifications_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ShopCartItem(BaseModel):
    """Схема элемента корзины"""
    product_id: int
    quantity: int


class ShopCartSummary(BaseModel):
    """Схема сводки корзины"""
    items: List[dict]
    total_items: int
    total_amount: Decimal