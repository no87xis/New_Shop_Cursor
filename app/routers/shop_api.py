"""
API для магазина
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import logging

from app.db import get_db
from app.models.product import Product
from app.models.order import ShopCart
from app.schemas.order import ShopCartSummary, ShopCartItem
from app.constants.delivery import calculate_delivery_cost, DeliveryOption

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/shop", tags=["shop"])


def get_session_id(request) -> str:
    """
    Получение ID сессии из запроса
    """
    session_id = request.session.get("session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
    return session_id


@router.get("/cart/count")
async def get_cart_count(request, db: Session = Depends(get_db)):
    """
    Получение количества товаров в корзине
    """
    try:
        session_id = get_session_id(request)
        count = db.query(ShopCart).filter(ShopCart.session_id == session_id).count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения количества товаров в корзине")


@router.post("/cart/add")
async def add_to_cart(
    product_id: int,
    quantity: int,
    request,
    db: Session = Depends(get_db)
):
    """
    Добавление товара в корзину
    """
    try:
        # Проверяем существование товара
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        if product.quantity < quantity:
            raise HTTPException(status_code=400, detail="Недостаточно товара на складе")
        
        session_id = get_session_id(request)
        
        # Проверяем, есть ли уже такой товар в корзине
        existing_item = db.query(ShopCart).filter(
            ShopCart.session_id == session_id,
            ShopCart.product_id == product_id
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
            db.add(cart_item)
        
        db.commit()
        
        return {"success": True, "message": "Товар добавлен в корзину"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка добавления товара в корзину")


@router.post("/cart/add-form")
async def add_to_cart_form(
    product_id: int = Form(...),
    quantity: int = Form(...),
    request=None,
    db: Session = Depends(get_db)
):
    """
    Добавление товара в корзину через form data
    """
    return await add_to_cart(product_id, quantity, request, db)


@router.put("/cart/update/{product_id}")
async def update_cart_item(
    product_id: int,
    quantity: int,
    request,
    db: Session = Depends(get_db)
):
    """
    Обновление количества товара в корзине
    """
    try:
        session_id = get_session_id(request)
        
        cart_item = db.query(ShopCart).filter(
            ShopCart.session_id == session_id,
            ShopCart.product_id == product_id
        ).first()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Товар не найден в корзине")
        
        if quantity <= 0:
            # Удаляем товар из корзины
            db.delete(cart_item)
        else:
            # Проверяем наличие товара на складе
            product = db.query(Product).filter(Product.id == product_id).first()
            if product and product.quantity < quantity:
                raise HTTPException(status_code=400, detail="Недостаточно товара на складе")
            
            cart_item.quantity = quantity
        
        db.commit()
        
        return {"success": True, "message": "Корзина обновлена"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка обновления корзины")


@router.delete("/cart/remove/{product_id}")
async def remove_from_cart(
    product_id: int,
    request,
    db: Session = Depends(get_db)
):
    """
    Удаление товара из корзины
    """
    try:
        session_id = get_session_id(request)
        
        cart_item = db.query(ShopCart).filter(
            ShopCart.session_id == session_id,
            ShopCart.product_id == product_id
        ).first()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Товар не найден в корзине")
        
        db.delete(cart_item)
        db.commit()
        
        return {"success": True, "message": "Товар удален из корзины"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка удаления товара из корзины")


@router.get("/cart")
async def get_cart(request, db: Session = Depends(get_db)):
    """
    Получение содержимого корзины
    """
    try:
        session_id = get_session_id(request)
        
        # Получаем товары в корзине
        cart_items = db.query(ShopCart).filter(ShopCart.session_id == session_id).all()
        
        # Подготавливаем данные
        items = []
        total_amount = 0
        
        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
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
        
        return ShopCartSummary(
            items=items,
            total_items=len(items),
            total_amount=total_amount
        )
        
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения корзины")


@router.delete("/cart/clear")
async def clear_cart(request, db: Session = Depends(get_db)):
    """
    Очистка корзины
    """
    try:
        session_id = get_session_id(request)
        
        db.query(ShopCart).filter(ShopCart.session_id == session_id).delete()
        db.commit()
        
        return {"success": True, "message": "Корзина очищена"}
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка очистки корзины")


@router.get("/products")
async def get_products(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    Получение списка товаров
    """
    try:
        query = db.query(Product)
        
        if status:
            query = query.filter(Product.availability_status == status)
        
        total = query.count()
        products = query.offset(skip).limit(limit).all()
        
        return {
            "products": products,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения товаров")


@router.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Получение товара по ID
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения товара")