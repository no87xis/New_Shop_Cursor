"""
Веб-интерфейс для управления уведомлениями
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db import get_db
from app.services.order_service import ShopOrderService
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")


def check_admin_access(request: Request):
    """Проверка прав администратора"""
    # Здесь должна быть проверка авторизации
    # Пока возвращаем True для разработки
    return True


@router.get("/admin/notifications", response_class=HTMLResponse)
async def notifications_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Панель управления уведомлениями
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        
        # Получаем готовые заказы
        ready_orders = shop_order_service.get_ready_for_pickup()
        
        # Получаем доступные шаблоны
        templates_list = whatsapp_service.get_available_templates()
        
        # Проверяем здоровье WhatsApp сервиса
        relay_health = await whatsapp_service.check_relay_health()
        
        context = {
            "request": request,
            "ready_orders": ready_orders,
            "templates": templates_list,
            "relay_health": relay_health,
            "test_mode": whatsapp_service.test_mode,
            "dry_run_enabled": whatsapp_service.dry_run_enabled
        }
        
        return templates.TemplateResponse("admin/notifications.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading notifications dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки панели уведомлений: {e}"
        })


@router.post("/admin/notifications/send-ready")
async def send_ready_notifications(
    request: Request,
    template_key: str = Form("arrived_v1"),
    dry_run: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Отправка уведомлений о готовности заказов
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        ready_orders = shop_order_service.get_ready_for_pickup()
        
        if not ready_orders:
            return RedirectResponse(
                url="/admin/notifications?message=no_ready_orders", 
                status_code=302
            )
        
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
            return RedirectResponse(
                url="/admin/notifications?message=no_recipients", 
                status_code=302
            )
        
        # Создаем запрос на отправку
        from app.schemas.notification import RecipientData, NotificationSendRequest
        notification_request = NotificationSendRequest(
            template_key=template_key,
            recipients=[RecipientData(**recipient) for recipient in recipients],
            dry_run=dry_run,
            batch_id=f"ready_orders_{len(recipients)}"
        )
        
        # Отправляем уведомления
        response = await whatsapp_service.send_notifications(notification_request)
        
        # Обновляем статус уведомлений для заказов
        if not dry_run and response.ok:
            for order in ready_orders:
                if order.consent_whatsapp and order.whatsapp_phone:
                    shop_order_service.mark_as_notified(order.id)
        
        # Перенаправляем с результатами
        message = f"sent_{response.total_sent}_failed_{response.total_failed}"
        return RedirectResponse(
            url=f"/admin/notifications?message={message}&batch_id={response.batch_id}", 
            status_code=302
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending ready notifications: {e}")
        return RedirectResponse(
            url="/admin/notifications?message=error", 
            status_code=302
        )


@router.get("/admin/notifications/test", response_class=HTMLResponse)
async def test_notifications(request: Request):
    """
    Страница тестирования уведомлений
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получаем доступные шаблоны
        templates_list = whatsapp_service.get_available_templates()
        
        context = {
            "request": request,
            "templates": templates_list,
            "test_phone": whatsapp_service.test_phone
        }
        
        return templates.TemplateResponse("admin/test_notifications.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading test notifications page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки страницы тестирования: {e}"
        })


@router.post("/admin/notifications/test-send")
async def test_send_notification(
    request: Request,
    phone: str = Form(...),
    template_key: str = Form("arrived_v1"),
    custom_message: Optional[str] = Form(None),
    dry_run: bool = Form(True)
):
    """
    Отправка тестового уведомления
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Создаем тестового получателя
        from app.schemas.notification import RecipientData, NotificationSendRequest
        
        recipient = RecipientData(
            phone=phone,
            name="Тестовый пользователь",
            orderId="TEST-001"
        )
        
        # Создаем запрос
        notification_request = NotificationSendRequest(
            template_key=template_key,
            message_override=custom_message,
            recipients=[recipient],
            dry_run=dry_run,
            batch_id="test_send"
        )
        
        # Отправляем
        response = await whatsapp_service.send_notifications(notification_request)
        
        # Перенаправляем с результатами
        message = f"test_sent_{response.total_sent}_failed_{response.total_failed}"
        return RedirectResponse(
            url=f"/admin/notifications/test?message={message}&batch_id={response.batch_id}", 
            status_code=302
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return RedirectResponse(
            url="/admin/notifications/test?message=error", 
            status_code=302
        )


@router.get("/admin/notifications/templates", response_class=HTMLResponse)
async def notification_templates(request: Request):
    """
    Страница управления шаблонами уведомлений
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получаем доступные шаблоны
        templates_list = whatsapp_service.get_available_templates()
        
        context = {
            "request": request,
            "templates": templates_list
        }
        
        return templates.TemplateResponse("admin/notification_templates.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading notification templates page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки страницы шаблонов: {e}"
        })