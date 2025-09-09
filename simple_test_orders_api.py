"""
Упрощенный API для создания тестовых заказов
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import logging
import random
from datetime import datetime

from app.db import get_db
from app.models.product import Product
from app.models.order import Order

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/test-orders", tags=["test-orders"])

@router.post("/create-random")
async def create_random_test_order(
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Создает случайный тестовый заказ
    """
    try:
        # Получаем случайный товар
        products = db.query(Product).filter(
            Product.availability_status == "IN_STOCK",
            Product.quantity > 0
        ).all()
        
        if not products:
            raise HTTPException(status_code=400, detail="Нет доступных товаров для заказа")
        
        # Выбираем случайный товар
        product = random.choice(products)
        
        # Генерируем данные клиента если не указаны
        if not customer_name:
            customer_name = f"Тестовый клиент {random.randint(1, 1000)}"
        
        if not customer_phone:
            customer_phone = f"+37529{random.randint(1000000, 9999999)}"
        
        # Создаем заказ
        order = Order(
            phone=customer_phone,
            customer_name=customer_name,
            client_city="Грозный",
            product_id=product.id,
            product_name=product.name,
            qty=random.randint(1, min(3, product.quantity)),
            unit_price_rub=product.sell_price_rub or 0,
            eur_rate=0,
            order_code=f"T{random.randint(100000, 999999)}",
            created_at=datetime.now()
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Уменьшаем количество товара
        product.quantity -= order.qty
        if product.quantity <= 0:
            product.availability_status = "OUT_OF_STOCK"
        db.commit()
        
        return {
            "success": True,
            "message": "Тестовый заказ успешно создан",
            "order_id": order.id,
            "order_code": order.order_code,
            "customer_name": order.customer_name,
            "customer_phone": order.phone,
            "product_name": order.product_name,
            "quantity": order.qty,
            "total_amount": float(order.unit_price_rub) * order.qty
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания тестового заказа: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания заказа: {e}")

@router.get("/generate-sample-data")
async def generate_sample_orders(
    count: int = 5,
    db: Session = Depends(get_db)
):
    """
    Генерирует несколько тестовых заказов для демонстрации
    """
    try:
        if count > 20:
            raise HTTPException(status_code=400, detail="Максимум 20 заказов за раз")
        
        created_orders = []
        
        for i in range(count):
            result = await create_random_test_order(
                customer_name=f"Демо клиент {i+1}",
                customer_phone=f"+37529{random.randint(1000000, 9999999)}",
                db=db
            )
            
            created_orders.append(result)
        
        return {
            "success": True,
            "message": f"Создано {count} тестовых заказов",
            "orders": created_orders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации тестовых данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации данных: {e}")

@router.get("/statistics")
async def get_test_orders_statistics(db: Session = Depends(get_db)):
    """
    Получает статистику по тестовым заказам
    """
    try:
        # Подсчитываем тестовые заказы (по коду заказа начинающемуся с T)
        test_orders = db.query(Order).filter(
            Order.order_code.like("T%")
        ).all()
        
        total_orders = len(test_orders)
        total_amount = sum(float(order.unit_price_rub) * order.qty for order in test_orders)
        
        # Последние заказы
        recent_orders = db.query(Order).filter(
            Order.order_code.like("T%")
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        return {
            "total_test_orders": total_orders,
            "total_amount": total_amount,
            "recent_orders": [
                {
                    "id": order.id,
                    "order_code": order.order_code,
                    "customer_name": order.customer_name,
                    "product_name": order.product_name,
                    "quantity": order.qty,
                    "total_amount": float(order.unit_price_rub) * order.qty,
                    "created_at": order.created_at.isoformat()
                }
                for order in recent_orders
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {e}")