from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.shop_cart import ShopCart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ShopCartService:
    """Сервис корзины магазина согласно ТЗ"""
    
    def __init__(self, db: Session):
        self.db = db

    def add_to_cart(self, session_id: str, product_id: int, quantity: int = 1):
        """Добавить товар в корзину согласно ТЗ"""
        try:
            # Получаем товар
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError("Товар не найден")
            
            # Проверяем статус товара согласно ТЗ
            if product.availability_status == 'OUT_OF_STOCK':
                raise ValueError("Товар отсутствует на складе")
            
            # Проверяем количество для товаров в наличии
            if product.availability_status == 'IN_STOCK' and product.quantity < quantity:
                raise ValueError("Недостаточно товара на складе")
            
            # Ищем существующий товар в корзине
            existing_item = self.db.query(ShopCart).filter(
                ShopCart.session_id == session_id,
                ShopCart.product_id == product_id
            ).first()
            
            if existing_item:
                # Обновляем количество
                existing_item.quantity += quantity
                existing_item.updated_at = datetime.utcnow()
            else:
                # Создаем новый элемент корзины
                cart_item = ShopCart(
                    session_id=session_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price_rub=float(product.sell_price_rub) if product.sell_price_rub else 0.0
                )
                self.db.add(cart_item)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            self.db.rollback()
            raise

    def get_cart_items(self, session_id: str):
        """Получить товары корзины"""
        try:
            cart_items = self.db.query(ShopCart).filter(
                ShopCart.session_id == session_id
            ).all()
            return cart_items
        except Exception as e:
            logger.error(f"Error getting cart items: {e}")
            return []

    def get_cart_count(self, session_id: str):
        """Получить количество товаров в корзине"""
        try:
            count = self.db.query(ShopCart).filter(
                ShopCart.session_id == session_id
            ).count()
            return count
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0

    def update_cart_item(self, session_id: str, product_id: int, quantity: int):
        """Обновить количество товара в корзине"""
        try:
            cart_item = self.db.query(ShopCart).filter(
                ShopCart.session_id == session_id,
                ShopCart.product_id == product_id
            ).first()
            
            if not cart_item:
                raise ValueError("Товар не найден в корзине")
            
            if quantity <= 0:
                # Удаляем товар из корзины
                self.db.delete(cart_item)
            else:
                # Проверяем наличие товара
                product = cart_item.product
                if product.availability_status == 'IN_STOCK' and product.quantity < quantity:
                    raise ValueError("Недостаточно товара на складе")
                
                cart_item.quantity = quantity
                cart_item.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            self.db.rollback()
            raise

    def remove_from_cart(self, session_id: str, product_id: int):
        """Удалить товар из корзины"""
        try:
            cart_item = self.db.query(ShopCart).filter(
                ShopCart.session_id == session_id,
                ShopCart.product_id == product_id
            ).first()
            
            if cart_item:
                self.db.delete(cart_item)
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            self.db.rollback()
            raise

    def clear_cart(self, session_id: str):
        """Очистить корзину (используется при создании заказа)"""
        try:
            self.db.query(ShopCart).filter(
                ShopCart.session_id == session_id
            ).delete()
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            self.db.rollback()
            raise

    def get_cart_total(self, session_id: str):
        """Получить общую сумму корзины"""
        try:
            cart_items = self.get_cart_items(session_id)
            total = sum(float(item.unit_price_rub * item.quantity) for item in cart_items)
            return total
        except Exception as e:
            logger.error(f"Error calculating cart total: {e}")
            return 0.0
