"""
Pydantic схемы для уведомлений - НОВОЕ
"""
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class RecipientData(BaseModel):
    """Данные получателя уведомления"""
    phone: str
    name: str
    orderId: Optional[str] = None
    order_uuid: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        """Валидация номера телефона"""
        # Убираем все нецифровые символы кроме +
        cleaned = re.sub(r'[^\d+]', '', v)
        if not cleaned:
            raise ValueError('Invalid phone number format')
        return cleaned
    
    @validator('name')
    def validate_name(cls, v):
        """Валидация имени"""
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if not re.match(r'^[a-zA-Zа-яА-Я\s\-_]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()


class NotificationSendRequest(BaseModel):
    """Запрос на отправку уведомлений"""
    template_key: str = "arrived_v1"
    message_override: Optional[str] = None
    default_country: str = "BY"
    rate: Dict[str, int] = {
        "per_minute": 45,
        "min_delay_ms": 900,
        "max_delay_ms": 1700
    }
    dry_run: bool = False
    recipients: List[RecipientData]
    template_vars: Dict[str, str] = {}
    batch_id: str
    
    @validator('recipients')
    def validate_recipients(cls, v):
        """Валидация получателей"""
        if not v:
            raise ValueError('At least one recipient required')
        if len(v) > 50:
            raise ValueError('Maximum 50 recipients allowed')
        return v


class NotificationSendResponse(BaseModel):
    """Ответ на отправку уведомлений"""
    ok: bool
    dry_run: bool
    batch_id: str
    results: List[Dict[str, Any]]
    total_sent: int
    total_failed: int
    total_skipped: int
    total_invalid: int


class ReadyOrderResponse(BaseModel):
    """Ответ с заказом готовым к выдаче"""
    id: int
    order_code: str
    customer_name: str
    customer_phone: str
    product_name: str
    quantity: int
    arrival_status: str
    arrival_notified_at: Optional[datetime] = None
    arrival_notifications_count: int = 0
    whatsapp_phone: Optional[str] = None
    consent_whatsapp: bool = True
    created_at: datetime


class NotificationResultsResponse(BaseModel):
    """Ответ с результатами рассылки"""
    batch_id: str
    total: int
    sent: int
    failed: int
    skipped: int
    invalid_phone: int
    results: List[Dict[str, Any]]
    created_at: datetime


class RetryFailedRequest(BaseModel):
    """Запрос на повторную отправку неудачных"""
    batch_id: str
    failed_ids: List[int]


class MessageTemplate(BaseModel):
    """Шаблон сообщения"""
    key: str
    name: str
    template: str
    description: str
    variables: List[str]


class PreviewRequest(BaseModel):
    """Запрос на превью сообщения"""
    template_key: str
    template_vars: Dict[str, str]
    recipient_data: RecipientData


class PreviewResponse(BaseModel):
    """Ответ с превью сообщения"""
    template_key: str
    message_text: str
    recipient_name: str
    recipient_phone: str