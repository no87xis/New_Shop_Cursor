"""
Модель логов уведомлений - НОВОЕ
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, func, BigInteger
from .base import BaseModel


class MessageLog(BaseModel):
    """Модель логов уведомлений"""
    __tablename__ = "message_logs"
    
    id = Column(BigInteger, primary_key=True, index=True)  # Переопределяем для BIGSERIAL
    batch_id = Column(String, nullable=False, index=True)  # идентификатор одной рассылки
    order_id = Column(Integer)  # связанный заказ (если есть)
    customer_id = Column(Integer)  # связанный клиент (если есть)
    phone_raw = Column(Text, nullable=False)  # исходный телефон
    phone_e164 = Column(Text)  # после нормализации
    template_key = Column(Text, nullable=False)  # например, 'arrived_v1'
    message_text = Column(Text, nullable=False)  # финальный текст
    status = Column(Text, nullable=False)  # 'sent' | 'fail' | 'skipped' | 'invalid_phone'
    wa_message_id = Column(Text)  # если отправлено
    error_text = Column(Text)  # если ошибка
    sent_at = Column(DateTime)  # время отправки
    retried_of_id = Column(BigInteger)  # ссылка на лог первой попытки, если это повтор
    
    def __repr__(self):
        return f"<MessageLog(batch_id='{self.batch_id}', phone='{self.phone_raw}', status='{self.status}')>"