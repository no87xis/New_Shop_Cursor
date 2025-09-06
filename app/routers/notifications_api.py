"""
API для WhatsApp уведомлений
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db import get_db
from app.models.order import ShopOrder
from app.schemas.notification import (
    NotificationSendRequest,
    NotificationSendResponse,
    ReadyOrderResponse,
    NotificationResultsResponse,
    RetryFailedRequest,
    MessageTemplate,
    PreviewRequest,
    PreviewResponse
)
from app.services.whatsapp_service import whatsapp_service
from app.services.order_service import ShopOrderService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def check_admin_access():
    """Проверка прав администратора"""
    # Здесь должна быть проверка авторизации
    # Пока возвращаем True для разработки
    return True


@router.get("/templates", response_model=List[MessageTemplate])
async def get_message_templates():
    """Получение доступных шаблонов сообщений"""
    try:
        templates = whatsapp_service.get_available_templates()
        return [
            MessageTemplate(
                key=template["key"],
                name=template["name"],
                template=template.get("template", ""),
                description=template["description"],
                variables=template["variables"]
            )
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error getting message templates: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения шаблонов")


@router.post("/preview", response_model=PreviewResponse)
async def preview_message(request: PreviewRequest):
    """Превью сообщения"""
    try:
        message_text = whatsapp_service.preview_message(
            request.template_key,
            request.template_vars,
            request.recipient_data
        )
        
        return PreviewResponse(
            template_key=request.template_key,
            message_text=message_text,
            recipient_name=request.recipient_data.name,
            recipient_phone=request.recipient_data.phone
        )
    except Exception as e:
        logger.error(f"Error previewing message: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания превью")


@router.get("/ready-orders", response_model=List[ReadyOrderResponse])
async def get_ready_orders(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Получение заказов готовых к выдаче"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        ready_orders = shop_order_service.get_ready_for_pickup()
        
        # Ограничиваем количество
        ready_orders = ready_orders[:limit]
        
        return [
            ReadyOrderResponse(
                id=order.id,
                order_code=order.order_code,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                product_name=order.product_name,
                quantity=order.quantity,
                arrival_status=order.arrival_status,
                arrival_notified_at=order.arrival_notified_at,
                arrival_notifications_count=order.arrival_notifications_count,
                whatsapp_phone=order.whatsapp_phone,
                consent_whatsapp=order.consent_whatsapp,
                created_at=order.created_at
            )
            for order in ready_orders
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ready orders: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения готовых заказов")


@router.post("/send", response_model=NotificationSendResponse)
async def send_notifications(request: NotificationSendRequest):
    """Отправка уведомлений"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Валидация запроса
        if not request.recipients:
            raise HTTPException(status_code=400, detail="Список получателей пуст")
        
        if len(request.recipients) > 50:
            raise HTTPException(status_code=400, detail="Максимум 50 получателей за раз")
        
        # Отправляем уведомления
        response = await whatsapp_service.send_notifications(request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки уведомлений")


@router.post("/send-ready-orders")
async def send_ready_orders_notifications(
    template_key: str = "arrived_v1",
    dry_run: bool = True,
    db: Session = Depends(get_db)
):
    """Отправка уведомлений о готовности заказов"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        ready_orders = shop_order_service.get_ready_for_pickup()
        
        if not ready_orders:
            return {
                "message": "Нет заказов готовых к выдаче",
                "sent_count": 0,
                "total_count": 0
            }
        
        # Подготавливаем получателей
        recipients = []
        for order in ready_orders:
            if order.consent_whatsapp and order.whatsapp_phone:
                recipients.append({
                    "phone": order.whatsapp_phone,
                    "name": order.customer_name,
                    "orderId": order.order_code,
                    "order_uuid": str(order.id)
                })
        
        if not recipients:
            return {
                "message": "Нет получателей с согласием на WhatsApp",
                "sent_count": 0,
                "total_count": len(ready_orders)
            }
        
        # Создаем запрос на отправку
        from app.schemas.notification import RecipientData
        request = NotificationSendRequest(
            template_key=template_key,
            recipients=[RecipientData(**recipient) for recipient in recipients],
            dry_run=dry_run,
            batch_id=f"ready_orders_{len(recipients)}"
        )
        
        # Отправляем уведомления
        response = await whatsapp_service.send_notifications(request)
        
        # Обновляем статус уведомлений для заказов
        if not dry_run and response.ok:
            for order in ready_orders:
                if order.consent_whatsapp and order.whatsapp_phone:
                    shop_order_service.mark_as_notified(order.id)
        
        return {
            "message": "Уведомления отправлены",
            "sent_count": response.total_sent,
            "failed_count": response.total_failed,
            "total_count": len(ready_orders),
            "batch_id": response.batch_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending ready orders notifications: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки уведомлений о готовности")


@router.get("/health")
async def check_whatsapp_health():
    """Проверка здоровья WhatsApp сервиса"""
    try:
        relay_health = await whatsapp_service.check_relay_health()
        
        return {
            "ok": relay_health,
            "relay_connected": relay_health,
            "service_ready": True,
            "test_mode": whatsapp_service.test_mode,
            "dry_run_enabled": whatsapp_service.dry_run_enabled
        }
    except Exception as e:
        logger.error(f"Error checking WhatsApp health: {e}")
        return {
            "ok": False,
            "relay_connected": False,
            "service_ready": False,
            "error": str(e)
        }


@router.get("/statistics")
async def get_notification_statistics(db: Session = Depends(get_db)):
    """Получение статистики уведомлений"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Здесь можно добавить статистику из базы данных
        # Пока возвращаем базовую информацию
        
        return {
            "templates_count": len(whatsapp_service.get_available_templates()),
            "relay_health": await whatsapp_service.check_relay_health(),
            "test_mode": whatsapp_service.test_mode,
            "dry_run_enabled": whatsapp_service.dry_run_enabled,
            "rate_limit_per_minute": whatsapp_service.rate_limit_per_minute
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification statistics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")


@router.post("/test-send")
async def test_send_notification(
    phone: str,
    message: str = "Тестовое сообщение от Sirius Group V2",
    dry_run: bool = True
):
    """Тестовая отправка уведомления"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        from app.schemas.notification import RecipientData, NotificationSendRequest
        
        # Создаем тестового получателя
        recipient = RecipientData(
            phone=phone,
            name="Тестовый пользователь",
            orderId="TEST-001"
        )
        
        # Создаем запрос
        request = NotificationSendRequest(
            template_key="arrived_v1",
            message_override=message,
            recipients=[recipient],
            dry_run=dry_run,
            batch_id="test_send"
        )
        
        # Отправляем
        response = await whatsapp_service.send_notifications(request)
        
        return {
            "message": "Тестовое уведомление отправлено",
            "result": response.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки тестового уведомления")