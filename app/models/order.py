"""
Модель заказа
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Date, Boolean, ForeignKey
from .base import BaseModel


class Order(BaseModel):
    """Модель заказа"""
    __tablename__ = "orders"
    
    phone = Column(String, nullable=False, index=True)
    customer_name = Column(String)
    client_city = Column(String(100))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String)  # денормализация для истории
    qty = Column(Integer, nullable=False)
    unit_price_rub = Column(Numeric(10, 2), nullable=False)
    eur_rate = Column(Numeric(10, 4), default=0)
    order_code = Column(String(8), unique=True, index=True)  # уникальный код заказа
    order_code_last4 = Column(String(4))  # последние 4 символа для поиска
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    payment_instrument_id = Column(Integer, ForeignKey("payment_instruments.id"))
    paid_amount = Column(Numeric(10, 2))
    paid_at = Column(DateTime)
    payment_method = Column(String, default="unpaid")  # card, cash, unpaid, other
    payment_note = Column(String(120))
    status = Column(String, default="paid_not_issued")  # различные статусы заказа
    arrival_status = Column(String(20), default="pending")  # НОВОЕ: Статус прибытия
    arrival_notified_at = Column(DateTime)  # НОВОЕ: Время уведомления
    arrival_notifications_count = Column(Integer, default=0)  # НОВОЕ: Количество уведомлений
    issued_at = Column(DateTime)
    user_id = Column(String, ForeignKey("users.username"))
    source = Column(String(20), default="manual")  # manual, shop
    qr_payload = Column(String)  # уникальный токен для QR-кода
    qr_image_path = Column(String)
    whatsapp_phone = Column(String(20))  # НОВОЕ: WhatsApp номер
    consent_whatsapp = Column(Boolean, default=True)  # НОВОЕ: Согласие на WA
    
    def __repr__(self):
        return f"<Order(code='{self.order_code}', customer='{self.customer_name}', status='{self.status}')>"


class ShopOrder(BaseModel):
    """Модель заказа магазина"""
    __tablename__ = "shop_orders"
    
    order_code = Column(String(8), unique=True, nullable=False, index=True)
    order_code_last4 = Column(String(4), nullable=False)
    customer_name = Column(String(200), nullable=False)
    customer_phone = Column(String(20), nullable=False, index=True)
    customer_city = Column(String(100))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_rub = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    payment_method_name = Column(String(100))
    delivery_option = Column(String(50))  # SELF_PICKUP_GROZNY, COURIER_GROZNY, etc.
    delivery_city_other = Column(String(100))
    delivery_cost_rub = Column(Numeric(10, 2))
    status = Column(String(20), default="ordered_not_paid")
    arrival_status = Column(String(20), default="pending")  # НОВОЕ: Статус прибытия
    arrival_notified_at = Column(DateTime)  # НОВОЕ: Время уведомления
    arrival_notifications_count = Column(Integer, default=0)  # НОВОЕ: Количество уведомлений
    reserved_until = Column(DateTime)
    expected_delivery_date = Column(Date)
    qr_payload = Column(String)
    qr_image_path = Column(String)
    whatsapp_phone = Column(String(20))  # НОВОЕ: WhatsApp номер
    consent_whatsapp = Column(Boolean, default=True)  # НОВОЕ: Согласие на WA
    
    def __repr__(self):
        return f"<ShopOrder(code='{self.order_code}', customer='{self.customer_name}', status='{self.status}')>"


class ShopCart(BaseModel):
    """Модель корзины магазина"""
    __tablename__ = "shop_cart"
    
    session_id = Column(String, nullable=False, index=True)  # ID сессии для корзины
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<ShopCart(session_id='{self.session_id}', product_id={self.product_id}, qty={self.quantity})>"


class PaymentMethod(BaseModel):
    """Модель способа оплаты"""
    __tablename__ = "payment_methods"
    
    name = Column(String, nullable=False)
    description = Column(String)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<PaymentMethod(name='{self.name}', active={self.is_active})>"


class PaymentInstrument(BaseModel):
    """Модель инструмента оплаты"""
    __tablename__ = "payment_instruments"
    
    name = Column(String, nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<PaymentInstrument(name='{self.name}', method_id={self.payment_method_id})>"