"""
Сервис для управления товарами
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
import logging

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ProductService(BaseService[Product, ProductCreate, ProductUpdate]):
    """Сервис для управления товарами"""
    
    def __init__(self, db: Session):
        super().__init__(Product, db)
    
    def get_by_name(self, name: str) -> Optional[Product]:
        """Получение товара по названию"""
        try:
            return self.db.query(Product).filter(Product.name == name).first()
        except Exception as e:
            logger.error(f"Error getting product by name {name}: {e}")
            return None
    
    def get_by_status(self, status: str) -> List[Product]:
        """Получение товаров по статусу"""
        try:
            return self.db.query(Product).filter(Product.availability_status == status).all()
        except Exception as e:
            logger.error(f"Error getting products by status {status}: {e}")
            return []
    
    def get_low_stock_products(self, min_stock: int = None) -> List[Product]:
        """Получение товаров с низким остатком"""
        try:
            query = self.db.query(Product)
            if min_stock is not None:
                query = query.filter(Product.quantity <= min_stock)
            else:
                query = query.filter(Product.quantity <= Product.min_stock)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return []
    
    def get_available_products(self) -> List[Product]:
        """Получение доступных товаров"""
        try:
            return self.db.query(Product).filter(
                and_(
                    Product.availability_status == "IN_STOCK",
                    Product.quantity > 0
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting available products: {e}")
            return []
    
    def search_products(self, search_term: str) -> List[Product]:
        """Поиск товаров по названию и описанию"""
        try:
            return self.db.query(Product).filter(
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%"),
                    Product.supplier_name.ilike(f"%{search_term}%")
                )
            ).all()
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def update_quantity(self, product_id: int, new_quantity: int) -> Optional[Product]:
        """Обновление количества товара"""
        try:
            product = self.get(product_id)
            if not product:
                return None
            
            product.quantity = new_quantity
            
            # Обновляем статус в зависимости от количества
            if new_quantity <= 0:
                product.availability_status = "OUT_OF_STOCK"
            elif new_quantity <= product.min_stock:
                product.availability_status = "LOW_STOCK"
            else:
                product.availability_status = "IN_STOCK"
            
            self.db.commit()
            self.db.refresh(product)
            logger.info(f"Updated product {product_id} quantity to {new_quantity}")
            return product
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating product quantity: {e}")
            return None
    
    def update_status(self, product_id: int, status: str) -> Optional[Product]:
        """Обновление статуса товара"""
        try:
            product = self.get(product_id)
            if not product:
                return None
            
            product.availability_status = status
            self.db.commit()
            self.db.refresh(product)
            logger.info(f"Updated product {product_id} status to {status}")
            return product
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating product status: {e}")
            return None
    
    def get_products_by_supplier(self, supplier_name: str) -> List[Product]:
        """Получение товаров по поставщику"""
        try:
            return self.db.query(Product).filter(
                Product.supplier_name == supplier_name
            ).all()
        except Exception as e:
            logger.error(f"Error getting products by supplier {supplier_name}: {e}")
            return []
    
    def get_products_in_price_range(self, min_price: float = None, max_price: float = None) -> List[Product]:
        """Получение товаров в диапазоне цен"""
        try:
            query = self.db.query(Product)
            
            if min_price is not None:
                query = query.filter(Product.sell_price_rub >= min_price)
            
            if max_price is not None:
                query = query.filter(Product.sell_price_rub <= max_price)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting products in price range: {e}")
            return []
    
    def get_popular_products(self, limit: int = 10) -> List[Product]:
        """Получение популярных товаров (по количеству заказов)"""
        try:
            # Здесь можно добавить логику подсчета популярности
            # Пока возвращаем товары с наибольшим количеством
            return self.db.query(Product).order_by(desc(Product.quantity)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting popular products: {e}")
            return []
    
    def get_recent_products(self, limit: int = 10) -> List[Product]:
        """Получение последних добавленных товаров"""
        try:
            return self.db.query(Product).order_by(desc(Product.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent products: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики по товарам"""
        try:
            total_products = self.count()
            in_stock = self.count({"availability_status": "IN_STOCK"})
            low_stock = len(self.get_low_stock_products())
            out_of_stock = self.count({"availability_status": "OUT_OF_STOCK"})
            
            # Общая стоимость товаров на складе
            products = self.db.query(Product).all()
            total_value = sum(
                float(product.sell_price_rub or 0) * product.quantity 
                for product in products
            )
            
            return {
                "total_products": total_products,
                "in_stock": in_stock,
                "low_stock": low_stock,
                "out_of_stock": out_of_stock,
                "total_value": total_value,
                "average_price": total_value / total_products if total_products > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting product statistics: {e}")
            return {}
    
    def bulk_update_status(self, product_ids: List[int], status: str) -> int:
        """Массовое обновление статуса товаров"""
        try:
            updated_count = self.db.query(Product).filter(
                Product.id.in_(product_ids)
            ).update(
                {"availability_status": status},
                synchronize_session=False
            )
            
            self.db.commit()
            logger.info(f"Bulk updated {updated_count} products status to {status}")
            return updated_count
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error bulk updating product status: {e}")
            return 0