"""
API для отслеживания заказов по QR-коду
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.qr_service import QRCodeService
from app.models.shop_order import ShopOrder
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/shop/order/track/{qr_token}")
async def track_order_by_qr(qr_token: str, db: Session = Depends(get_db)):
    """
    Получить информацию о заказе по QR-токену
    """
    try:
        order = QRCodeService.get_order_by_qr_token(db, qr_token)
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Формируем ответ с информацией о заказе
        order_data = {
            "order_code": order.order_code,
            "status": order.status,
            "status_display": order.get_status_display(),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "delivery_option": order.delivery_option,
            "payment_method": order.payment_method.name if order.payment_method else None,
            "total_amount": float(order.total_amount),
            "delivery_cost_rub": float(order.delivery_cost_rub),
            "payment_percentage": float(order.payment_percentage),
            "created_at": order.created_at.isoformat(),
            "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
            "products": [
                {
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price_rub),
                    "total_price": float(item.quantity * item.unit_price_rub)
                }
                for item in order.order_items
            ]
        }
        
        return {
            "success": True,
            "order": order_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения заказа по QR-токену: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/api/shop/order/{order_code}/qr-info")
async def get_qr_info(order_code: str, db: Session = Depends(get_db)):
    """
    Получить QR-информацию заказа по коду заказа
    """
    try:
        order = db.query(ShopOrder).filter(ShopOrder.order_code == order_code).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        return {
            "success": True,
            "qr_token": order.qr_token,
            "qr_code_path": order.qr_code_path,
            "tracking_url": f"http://185.239.50.157:8000/shop/o/{order.qr_token}" if order.qr_token else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения QR-информации: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")