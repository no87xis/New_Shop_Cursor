"""
Сервис для управления заказами
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, date
import logging

from app.models.order import Order, ShopOrder, ShopCart
from app.schemas.order import OrderCreate, OrderUpdate, ShopOrderCreate, ShopOrderUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class OrderService(BaseService[Order, OrderCreate, OrderUpdate]):
    """Сервис для управления заказами"""
    
    def __init__(self, db: Session):
        super().__init__(Order, db)
    
    def get_by_code(self, order_code: str) -> Optional[Order]:
        """Получение заказа по коду"""
        try:
            return self.db.query(Order).filter(Order.order_code == order_code).first()
        except Exception as e:
            logger.error(f"Error getting order by code {order_code}: {e}")
            return None
    
    def get_by_phone(self, phone: str) -> List[Order]:
        """Получение заказов по телефону"""
        try:
            return self.db.query(Order).filter(Order.phone == phone).all()
        except Exception as e:
            logger.error(f"Error getting orders by phone {phone}: {e}")
            return []
    
    def get_by_status(self, status: str) -> List[Order]:
        """Получение заказов по статусу"""
        try:
            return self.db.query(Order).filter(Order.status == status).all()
        except Exception as e:
            logger.error(f"Error getting orders by status {status}: {e}")
            return []
    
    def get_by_user(self, user_id: str) -> List[Order]:
        """Получение заказов пользователя"""
        try:
            return self.db.query(Order).filter(Order.user_id == user_id).all()
        except Exception as e:
            logger.error(f"Error getting orders by user {user_id}: {e}")
            return []
    
    def update_status(self, order_id: int, status: str) -> Optional[Order]:
        """Обновление статуса заказа"""
        try:
            order = self.get(order_id)
            if not order:
                return None
            
            order.status = status
            if status in ["paid_issued", "self_pickup"]:
                order.issued_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(order)
            logger.info(f"Updated order {order_id} status to {status}")
            return order
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating order status: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по заказам"""
        try:
            total_orders = self.count()
            
            # Статистика по статусам
            status_stats = {}
            for status in ["unpaid", "paid_not_issued", "paid_issued", "self_pickup"]:
                status_stats[status] = self.count({"status": status})
            
            # Общая сумма заказов
            orders = self.db.query(Order).all()
            total_amount = sum(
                float(order.unit_price_rub or 0) * order.qty 
                for order in orders
            )
            
            # Заказы за последние 30 дней
            thirty_days_ago = datetime.now().date()
            recent_orders = self.db.query(Order).filter(
                func.date(Order.created_at) >= thirty_days_ago
            ).count()
            
            return {
                "total_orders": total_orders,
                "status_stats": status_stats,
                "total_amount": total_amount,
                "recent_orders": recent_orders,
                "average_order_value": total_amount / total_orders if total_orders > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            return {}


class ShopOrderService(BaseService[ShopOrder, ShopOrderCreate, ShopOrderUpdate]):
    """Сервис для управления заказами магазина"""
    
    def __init__(self, db: Session):
        super().__init__(ShopOrder, db)
    
    def get_by_code(self, order_code: str) -> Optional[ShopOrder]:
        """Получение заказа по коду"""
        try:
            return self.db.query(ShopOrder).filter(ShopOrder.order_code == order_code).first()
        except Exception as e:
            logger.error(f"Error getting shop order by code {order_code}: {e}")
            return None
    
    def get_by_phone(self, phone: str) -> List[ShopOrder]:
        """Получение заказов по телефону"""
        try:
            return self.db.query(ShopOrder).filter(ShopOrder.customer_phone == phone).all()
        except Exception as e:
            logger.error(f"Error getting shop orders by phone {phone}: {e}")
            return []
    
    def get_by_status(self, status: str) -> List[ShopOrder]:
        """Получение заказов по статусу"""
        try:
            return self.db.query(ShopOrder).filter(ShopOrder.status == status).all()
        except Exception as e:
            logger.error(f"Error getting shop orders by status {status}: {e}")
            return []
    
    def get_ready_for_pickup(self) -> List[ShopOrder]:
        """Получение заказов готовых к выдаче"""
        try:
            return self.db.query(ShopOrder).filter(
                and_(
                    ShopOrder.status == "ready_for_pickup",
                    ShopOrder.arrival_status == "ready"
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting ready for pickup orders: {e}")
            return []
    
    def update_status(self, order_id: int, status: str) -> Optional[ShopOrder]:
        """Обновление статуса заказа"""
        try:
            order = self.get(order_id)
            if not order:
                return None
            
            order.status = status
            self.db.commit()
            self.db.refresh(order)
            logger.info(f"Updated shop order {order_id} status to {status}")
            return order
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating shop order status: {e}")
            return None
    
    def update_arrival_status(self, order_id: int, arrival_status: str) -> Optional[ShopOrder]:
        """Обновление статуса прибытия заказа"""
        try:
            order = self.get(order_id)
            if not order:
                return None
            
            order.arrival_status = arrival_status
            if arrival_status == "ready":
                order.arrival_notified_at = None  # Сбрасываем время уведомления
            
            self.db.commit()
            self.db.refresh(order)
            logger.info(f"Updated shop order {order_id} arrival status to {arrival_status}")
            return order
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating shop order arrival status: {e}")
            return None
    
    def mark_as_notified(self, order_id: int) -> Optional[ShopOrder]:
        """Отметить заказ как уведомленный"""
        try:
            order = self.get(order_id)
            if not order:
                return None
            
            order.arrival_notified_at = datetime.now()
            order.arrival_notifications_count += 1
            
            self.db.commit()
            self.db.refresh(order)
            logger.info(f"Marked shop order {order_id} as notified")
            return order
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking shop order as notified: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по заказам магазина"""
        try:
            total_orders = self.count()
            
            # Статистика по статусам
            status_stats = {}
            for status in ["ordered_not_paid", "paid", "ready_for_pickup", "completed"]:
                status_stats[status] = self.count({"status": status})
            
            # Общая сумма заказов
            orders = self.db.query(ShopOrder).all()
            total_amount = sum(float(order.total_amount or 0) for order in orders)
            
            # Заказы за последние 30 дней
            thirty_days_ago = datetime.now().date()
            recent_orders = self.db.query(ShopOrder).filter(
                func.date(ShopOrder.created_at) >= thirty_days_ago
            ).count()
            
            return {
                "total_orders": total_orders,
                "status_stats": status_stats,
                "total_amount": total_amount,
                "recent_orders": recent_orders,
                "average_order_value": total_amount / total_orders if total_orders > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting shop order statistics: {e}")
            return {}


class ShopCartService:
    """Сервис для управления корзиной магазина"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_cart_items(self, session_id: str) -> List[ShopCart]:
        """Получение товаров в корзине"""
        try:
            return self.db.query(ShopCart).filter(ShopCart.session_id == session_id).all()
        except Exception as e:
            logger.error(f"Error getting cart items for session {session_id}: {e}")
            return []
    
    def add_to_cart(self, session_id: str, product_id: int, quantity: int) -> bool:
        """Добавление товара в корзину"""
        try:
            # Проверяем, есть ли уже такой товар в корзине
            existing_item = self.db.query(ShopCart).filter(
                and_(
                    ShopCart.session_id == session_id,
                    ShopCart.product_id == product_id
                )
            ).first()
            
            if existing_item:
                # Обновляем количество
                existing_item.quantity += quantity
            else:
                # Создаем новый элемент корзины
                cart_item = ShopCart(
                    session_id=session_id,
                    product_id=product_id,
                    quantity=quantity
                )
                self.db.add(cart_item)
            
            self.db.commit()
            logger.info(f"Added product {product_id} to cart for session {session_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding to cart: {e}")
            return False
    
    def update_quantity(self, session_id: str, product_id: int, quantity: int) -> bool:
        """Обновление количества товара в корзине"""
        try:
            cart_item = self.db.query(ShopCart).filter(
                and_(
                    ShopCart.session_id == session_id,
                    ShopCart.product_id == product_id
                )
            ).first()
            
            if not cart_item:
                return False
            
            if quantity <= 0:
                # Удаляем товар из корзины
                self.db.delete(cart_item)
            else:
                cart_item.quantity = quantity
            
            self.db.commit()
            logger.info(f"Updated cart item quantity for session {session_id}, product {product_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating cart quantity: {e}")
            return False
    
    def remove_from_cart(self, session_id: str, product_id: int) -> bool:
        """Удаление товара из корзины"""
        try:
            cart_item = self.db.query(ShopCart).filter(
                and_(
                    ShopCart.session_id == session_id,
                    ShopCart.product_id == product_id
                )
            ).first()
            
            if not cart_item:
                return False
            
            self.db.delete(cart_item)
            self.db.commit()
            logger.info(f"Removed product {product_id} from cart for session {session_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing from cart: {e}")
            return False
    
    def clear_cart(self, session_id: str) -> bool:
        """Очистка корзины"""
        try:
            self.db.query(ShopCart).filter(ShopCart.session_id == session_id).delete()
            self.db.commit()
            logger.info(f"Cleared cart for session {session_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing cart: {e}")
            return False
    
    def get_cart_count(self, session_id: str) -> int:
        """Получение количества товаров в корзине"""
        try:
            return self.db.query(ShopCart).filter(ShopCart.session_id == session_id).count()
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0
    
    def get_cart_summary(self, session_id: str) -> Dict[str, Any]:
        """Получение сводки корзины"""
        try:
            from app.models.product import Product
            
            cart_items = self.get_cart_items(session_id)
            items = []
            total_amount = 0
            
            for item in cart_items:
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    item_total = float(product.sell_price_rub or 0) * item.quantity
                    items.append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity": item.quantity,
                        "unit_price_rub": float(product.sell_price_rub or 0),
                        "total_price": item_total
                    })
                    total_amount += item_total
            
            return {
                "items": items,
                "total_items": len(items),
                "total_amount": total_amount
            }
        except Exception as e:
            logger.error(f"Error getting cart summary: {e}")
            return {"items": [], "total_items": 0, "total_amount": 0}