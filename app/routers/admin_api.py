"""
API для администрирования
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db import get_db
from app.models.product import Product
from app.models.order import Order, ShopOrder
from app.schemas.product import ProductCreate, ProductUpdate, Product as ProductSchema
from app.schemas.order import OrderUpdate, ShopOrderUpdate, ShopOrder as ShopOrderSchema
from app.services.product_service import ProductService
from app.services.order_service import OrderService, ShopOrderService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


def check_admin_access():
    """Проверка прав администратора"""
    # Здесь должна быть проверка авторизации
    # Пока возвращаем True для разработки
    return True


# API для товаров
@router.get("/products", response_model=List[ProductSchema])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Получение списка товаров"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        
        if search:
            products = product_service.search_products(search)
        else:
            filters = {}
            if status:
                filters["availability_status"] = status
            products = product_service.get_multi(skip=skip, limit=limit, filters=filters)
        
        return products
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения товаров")


@router.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Получение товара по ID"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.get(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения товара")


@router.post("/products", response_model=ProductSchema)
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Создание нового товара"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        
        # Проверяем, что товар с таким названием не существует
        existing_product = product_service.get_by_name(product_data.name)
        if existing_product:
            raise HTTPException(status_code=400, detail="Товар с таким названием уже существует")
        
        product = product_service.create(product_data)
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания товара")


@router.put("/products/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int, 
    product_data: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """Обновление товара"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.update(product_id, product_data)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления товара")


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Удаление товара"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        success = product_service.delete(product_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return {"message": "Товар удален успешно"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления товара")


@router.put("/products/{product_id}/quantity")
async def update_product_quantity(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    """Обновление количества товара"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.update_quantity(product_id, quantity)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product quantity: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления количества товара")


@router.put("/products/{product_id}/status")
async def update_product_status(
    product_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Обновление статуса товара"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.update_status(product_id, status)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product status: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса товара")


# API для заказов магазина
@router.get("/shop-orders", response_model=List[ShopOrderSchema])
async def get_shop_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Получение списка заказов магазина"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        
        if search:
            # Поиск по коду заказа или телефону
            orders = db.query(ShopOrder).filter(
                (ShopOrder.order_code.ilike(f"%{search}%")) |
                (ShopOrder.customer_phone.ilike(f"%{search}%")) |
                (ShopOrder.customer_name.ilike(f"%{search}%"))
            ).all()
        else:
            filters = {}
            if status:
                filters["status"] = status
            orders = shop_order_service.get_multi(skip=skip, limit=limit, filters=filters)
        
        return orders
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shop orders: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения заказов")


@router.get("/shop-orders/{order_id}", response_model=ShopOrderSchema)
async def get_shop_order(order_id: int, db: Session = Depends(get_db)):
    """Получение заказа магазина по ID"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        order = shop_order_service.get(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shop order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения заказа")


@router.put("/shop-orders/{order_id}/status")
async def update_shop_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Обновление статуса заказа магазина"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        order = shop_order_service.update_status(order_id, status)
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shop order status: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса заказа")


@router.put("/shop-orders/{order_id}/arrival-status")
async def update_shop_order_arrival_status(
    order_id: int,
    arrival_status: str,
    db: Session = Depends(get_db)
):
    """Обновление статуса прибытия заказа"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        order = shop_order_service.update_arrival_status(order_id, arrival_status)
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shop order arrival status: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса прибытия заказа")


# API для статистики
@router.get("/statistics/products")
async def get_product_statistics(db: Session = Depends(get_db)):
    """Получение статистики по товарам"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        stats = product_service.get_statistics()
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product statistics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики товаров")


@router.get("/statistics/orders")
async def get_order_statistics(db: Session = Depends(get_db)):
    """Получение статистики по заказам"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        order_stats = order_service.get_statistics()
        shop_order_stats = shop_order_service.get_statistics()
        
        return {
            "orders": order_stats,
            "shop_orders": shop_order_stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order statistics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики заказов")


@router.get("/statistics/overview")
async def get_overview_statistics(db: Session = Depends(get_db)):
    """Получение общей статистики"""
    try:
        if not check_admin_access():
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        return {
            "products": product_service.get_statistics(),
            "orders": order_service.get_statistics(),
            "shop_orders": shop_order_service.get_statistics()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting overview statistics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения общей статистики")