"""
API endpoints для создания тестовых заказов
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import random
from datetime import datetime, timedelta

from app.db import get_db
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.cart import CartItem
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/test-orders", tags=["test-orders"])

@router.post("/create-random")
async def create_random_test_order(
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    items_count: int = 3,
    db: Session = Depends(get_db)
):
    """
    Создает случайный тестовый заказ
    """
    try:
        # Получаем случайные товары
        products = db.query(Product).filter(
            Product.availability_status == "IN_STOCK",
            Product.quantity > 0
        ).all()
        
        if not products:
            raise HTTPException(status_code=400, detail="Нет доступных товаров для заказа")
        
        # Выбираем случайные товары
        selected_products = random.sample(products, min(items_count, len(products)))
        
        # Генерируем данные клиента если не указаны
        if not customer_name:
            customer_name = f"Тестовый клиент {random.randint(1, 1000)}"
        
        if not customer_phone:
            customer_phone = f"+37529{random.randint(1000000, 9999999)}"
        
        # Создаем заказ
        order_data = OrderCreate(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=f"test{random.randint(1, 1000)}@example.com",
            delivery_address=f"Тестовый адрес {random.randint(1, 100)}",
            notes=f"Тестовый заказ создан {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            status="PENDING"
        )
        
        # Создаем заказ в базе данных
        order = Order(
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            customer_email=order_data.customer_email,
            delivery_address=order_data.delivery_address,
            notes=order_data.notes,
            status=order_data.status,
            total_amount=0,
            created_at=datetime.now()
        )
        
        db.add(order)
        db.flush()  # Получаем ID заказа
        
        # Добавляем товары в заказ
        total_amount = 0
        for product in selected_products:
            quantity = random.randint(1, min(3, product.quantity))
            item_price = float(product.sell_price_rub or 0) * quantity
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                price=product.sell_price_rub,
                total_price=item_price
            )
            
            db.add(order_item)
            total_amount += item_price
            
            # Уменьшаем количество товара на складе
            product.quantity -= quantity
            if product.quantity <= 0:
                product.availability_status = "OUT_OF_STOCK"
        
        # Обновляем общую сумму заказа
        order.total_amount = total_amount
        db.commit()
        db.refresh(order)
        
        # Отправляем уведомление в WhatsApp
        try:
            message = f"""🛍️ Новый заказ #{order.id}

👤 Клиент: {order.customer_name}
📞 Телефон: {order.customer_phone}
📍 Адрес: {order.delivery_address}

📦 Товары:
"""
            for item in order.items:
                message += f"• {item.product.name} x{item.quantity} = {item.total_price:.0f} ₽\n"
            
            message += f"""
💰 Общая сумма: {order.total_amount:.0f} ₽
📝 Примечания: {order.notes or 'Нет'}
⏰ Время: {order.created_at.strftime('%Y-%m-%d %H:%M')}

Это тестовый заказ для проверки системы."""
            
            await whatsapp_service.send_notification(
                phone=order.customer_phone,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки WhatsApp уведомления: {e}")
        
        return {
            "success": True,
            "message": "Тестовый заказ успешно создан",
            "order_id": order.id,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "total_amount": order.total_amount,
            "items_count": len(selected_products)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания тестового заказа: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания заказа: {e}")

@router.post("/create-from-cart")
async def create_test_order_from_cart(
    customer_name: str,
    customer_phone: str,
    delivery_address: str,
    customer_email: Optional[str] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Создает тестовый заказ из существующей корзины
    """
    try:
        # Получаем все товары в корзине
        cart_items = db.query(CartItem).all()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Корзина пуста")
        
        # Создаем заказ
        order = Order(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email or f"test{random.randint(1, 1000)}@example.com",
            delivery_address=delivery_address,
            notes=notes or "Тестовый заказ из корзины",
            status="PENDING",
            total_amount=0,
            created_at=datetime.now()
        )
        
        db.add(order)
        db.flush()
        
        # Добавляем товары из корзины в заказ
        total_amount = 0
        for cart_item in cart_items:
            if cart_item.product.quantity >= cart_item.quantity:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price=cart_item.product.sell_price_rub,
                    total_price=float(cart_item.product.sell_price_rub or 0) * cart_item.quantity
                )
                
                db.add(order_item)
                total_amount += order_item.total_price
                
                # Уменьшаем количество товара
                cart_item.product.quantity -= cart_item.quantity
                if cart_item.product.quantity <= 0:
                    cart_item.product.availability_status = "OUT_OF_STOCK"
        
        # Обновляем общую сумму
        order.total_amount = total_amount
        db.commit()
        db.refresh(order)
        
        # Очищаем корзину
        db.query(CartItem).delete()
        db.commit()
        
        return {
            "success": True,
            "message": "Тестовый заказ из корзины создан",
            "order_id": order.id,
            "total_amount": order.total_amount,
            "items_count": len(cart_items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания заказа из корзины: {e}")
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
            # Создаем заказ с задержкой
            if i > 0:
                await asyncio.sleep(0.1)
            
            result = await create_random_test_order(
                customer_name=f"Демо клиент {i+1}",
                customer_phone=f"+37529{random.randint(1000000, 9999999)}",
                items_count=random.randint(1, 4),
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
        # Подсчитываем тестовые заказы (по примечаниям)
        test_orders = db.query(Order).filter(
            Order.notes.like("%тестовый%") | Order.notes.like("%Тестовый%")
        ).all()
        
        total_orders = len(test_orders)
        total_amount = sum(order.total_amount for order in test_orders)
        
        # Статистика по статусам
        status_stats = {}
        for order in test_orders:
            status_stats[order.status] = status_stats.get(order.status, 0) + 1
        
        # Последние заказы
        recent_orders = db.query(Order).filter(
            Order.notes.like("%тестовый%") | Order.notes.like("%Тестовый%")
        ).order_by(Order.created_at.desc()).limit(5).all()
        
        return {
            "total_test_orders": total_orders,
            "total_amount": total_amount,
            "status_distribution": status_stats,
            "recent_orders": [
                {
                    "id": order.id,
                    "customer_name": order.customer_name,
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "created_at": order.created_at.isoformat()
                }
                for order in recent_orders
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {e}")