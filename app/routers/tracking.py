"""
Роутер для отслеживания заказов
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db import get_db
from app.models.order import Order, ShopOrder
from app.services.qr_service import qr_service
from app.services.order_service import OrderService, ShopOrderService

logger = logging.getLogger(__name__)
router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")


@router.get("/track/{order_code}", response_class=HTMLResponse)
async def track_order(
    request: Request,
    order_code: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Страница отслеживания заказа
    """
    try:
        # Ищем заказ в обеих таблицах
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        # Сначала ищем в заказах магазина
        order = shop_order_service.get_by_code(order_code)
        order_type = "shop_order"
        
        if not order:
            # Если не найден в заказах магазина, ищем в обычных заказах
            order = order_service.get_by_code(order_code)
            order_type = "order"
        
        if not order:
            return templates.TemplateResponse("tracking/order_not_found.html", {
                "request": request,
                "order_code": order_code
            })
        
        # Валидация токена (если передан)
        if token:
            qr_data = f"{order_type}:{order_code}:{token}"
            if not qr_service.validate_qr_token(qr_data, order_type):
                return templates.TemplateResponse("tracking/invalid_token.html", {
                    "request": request,
                    "order_code": order_code
                })
        
        # Определяем статус заказа
        status_info = get_order_status_info(order, order_type)
        
        context = {
            "request": request,
            "order": order,
            "order_type": order_type,
            "status_info": status_info,
            "has_token": token is not None
        }
        
        return templates.TemplateResponse("tracking/order_status.html", context)
        
    except Exception as e:
        logger.error(f"Error tracking order {order_code}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка отслеживания заказа: {e}"
        })


@router.get("/track/{order_code}/qr", response_class=HTMLResponse)
async def track_order_qr(
    request: Request,
    order_code: str,
    db: Session = Depends(get_db)
):
    """
    Страница отслеживания заказа с QR-кодом
    """
    try:
        # Ищем заказ в обеих таблицах
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        # Сначала ищем в заказах магазина
        order = shop_order_service.get_by_code(order_code)
        order_type = "shop_order"
        
        if not order:
            # Если не найден в заказах магазина, ищем в обычных заказах
            order = order_service.get_by_code(order_code)
            order_type = "order"
        
        if not order:
            return templates.TemplateResponse("tracking/order_not_found.html", {
                "request": request,
                "order_code": order_code
            })
        
        # Генерируем QR-код
        if order_type == "shop_order":
            qr_data = qr_service.generate_shop_order_qr_code(order_code, order.id)
        else:
            qr_data = qr_service.generate_order_qr_code(order_code, order.id)
        
        if not qr_data:
            raise HTTPException(status_code=500, detail="Ошибка генерации QR-кода")
        
        # Определяем статус заказа
        status_info = get_order_status_info(order, order_type)
        
        context = {
            "request": request,
            "order": order,
            "order_type": order_type,
            "status_info": status_info,
            "qr_data": qr_data
        }
        
        return templates.TemplateResponse("tracking/order_qr.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking order with QR {order_code}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка отслеживания заказа: {e}"
        })


@router.get("/api/track/{order_code}")
async def track_order_api(
    order_code: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    API для отслеживания заказа
    """
    try:
        # Ищем заказ в обеих таблицах
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        # Сначала ищем в заказах магазина
        order = shop_order_service.get_by_code(order_code)
        order_type = "shop_order"
        
        if not order:
            # Если не найден в заказах магазина, ищем в обычных заказах
            order = order_service.get_by_code(order_code)
            order_type = "order"
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Валидация токена (если передан)
        if token:
            qr_data = f"{order_type}:{order_code}:{token}"
            if not qr_service.validate_qr_token(qr_data, order_type):
                raise HTTPException(status_code=403, detail="Неверный токен")
        
        # Определяем статус заказа
        status_info = get_order_status_info(order, order_type)
        
        return {
            "order_code": order_code,
            "order_type": order_type,
            "status": status_info["status"],
            "status_text": status_info["status_text"],
            "status_description": status_info["status_description"],
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat() if order.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking order API {order_code}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отслеживания заказа")


def get_order_status_info(order, order_type: str) -> dict:
    """
    Получение информации о статусе заказа
    
    Args:
        order: Объект заказа
        order_type: Тип заказа (order или shop_order)
        
    Returns:
        Словарь с информацией о статусе
    """
    try:
        if order_type == "shop_order":
            status = order.status
            arrival_status = getattr(order, 'arrival_status', None)
            
            # Определяем статус и описание
            if status == "ordered_not_paid":
                return {
                    "status": "pending_payment",
                    "status_text": "Ожидает оплаты",
                    "status_description": "Заказ создан, ожидается оплата",
                    "color": "yellow"
                }
            elif status == "paid":
                if arrival_status == "pending":
                    return {
                        "status": "paid_pending",
                        "status_text": "Оплачен, ожидает поступления",
                        "status_description": "Заказ оплачен, товар ожидается на складе",
                        "color": "blue"
                    }
                elif arrival_status == "ready":
                    return {
                        "status": "ready_for_pickup",
                        "status_text": "Готов к выдаче",
                        "status_description": "Товар поступил на склад и готов к выдаче",
                        "color": "green"
                    }
                else:
                    return {
                        "status": "paid",
                        "status_text": "Оплачен",
                        "status_description": "Заказ оплачен, обрабатывается",
                        "color": "blue"
                    }
            elif status == "ready_for_pickup":
                return {
                    "status": "ready_for_pickup",
                    "status_text": "Готов к выдаче",
                    "status_description": "Товар готов к выдаче",
                    "color": "green"
                }
            elif status == "completed":
                return {
                    "status": "completed",
                    "status_text": "Завершен",
                    "status_description": "Заказ успешно завершен",
                    "color": "green"
                }
            else:
                return {
                    "status": "unknown",
                    "status_text": "Неизвестный статус",
                    "status_description": f"Статус: {status}",
                    "color": "gray"
                }
        else:
            # Обычные заказы
            status = order.status
            
            if status == "unpaid":
                return {
                    "status": "unpaid",
                    "status_text": "Не оплачен",
                    "status_description": "Заказ создан, ожидается оплата",
                    "color": "red"
                }
            elif status == "paid_not_issued":
                return {
                    "status": "paid_not_issued",
                    "status_text": "Оплачен, не выдан",
                    "status_description": "Заказ оплачен, ожидает выдачи",
                    "color": "blue"
                }
            elif status == "paid_issued":
                return {
                    "status": "paid_issued",
                    "status_text": "Оплачен и выдан",
                    "status_description": "Заказ успешно завершен",
                    "color": "green"
                }
            elif status == "self_pickup":
                return {
                    "status": "self_pickup",
                    "status_text": "Самовывоз",
                    "status_description": "Заказ готов к самовывозу",
                    "color": "green"
                }
            else:
                return {
                    "status": "unknown",
                    "status_text": "Неизвестный статус",
                    "status_description": f"Статус: {status}",
                    "color": "gray"
                }
                
    except Exception as e:
        logger.error(f"Error getting order status info: {e}")
        return {
            "status": "error",
            "status_text": "Ошибка",
            "status_description": "Ошибка определения статуса заказа",
            "color": "red"
        }