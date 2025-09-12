from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.shop_cart_service import ShopCartService
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/shop/cart", tags=["Shop Cart API"])

def get_session_id(request: Request):
    """Получить или создать session_id"""
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/add")
async def add_to_cart(
    product_id: int,
    quantity: int = 1,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Добавить товар в корзину согласно ТЗ"""
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        cart_service.add_to_cart(session_id, product_id, quantity)
        
        response = JSONResponse(content={"success": True, "message": "Товар добавлен в корзину"})
        response.set_cookie(key="session_id", value=session_id, max_age=86400, httponly=True, samesite="lax")
        return response
        
    except ValueError as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail="Ошибка добавления в корзину")

@router.get("/items")
async def get_cart_items(request: Request, db: Session = Depends(get_db)):
    """Получить товары корзины"""
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        cart_items = cart_service.get_cart_items(session_id)
        
        items_data = []
        for item in cart_items:
            items_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "Неизвестный товар",
                "quantity": item.quantity,
                "unit_price_rub": float(item.unit_price_rub),
                "total_price_rub": float(item.unit_price_rub * item.quantity),
                "photo_url": item.product.get_photo_url() if item.product else "/static/images/placeholder-product.svg",
                "availability_status": item.product.availability_status if item.product else "UNKNOWN"
            })
        
        total_amount = cart_service.get_cart_total(session_id)
        
        return {
            "items": items_data,
            "total_amount": total_amount,
            "count": len(items_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting cart items: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки корзины")

@router.get("/count")
async def get_cart_count(request: Request, db: Session = Depends(get_db)):
    """Получить количество товаров в корзине"""
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        count = cart_service.get_cart_count(session_id)
        return {"count": count}
        
    except Exception as e:
        logger.error(f"Error getting cart count: {e}")
        return {"count": 0}

@router.put("/update/{product_id}")
async def update_cart_item(
    product_id: int,
    quantity: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Обновить количество товара в корзине"""
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        cart_service.update_cart_item(session_id, product_id, quantity)
        
        return {"success": True, "message": "Корзина обновлена"}
        
    except ValueError as e:
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления корзины")

@router.delete("/remove/{product_id}")
async def remove_from_cart(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Удалить товар из корзины"""
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        cart_service.remove_from_cart(session_id, product_id)
        
        return {"success": True, "message": "Товар удален из корзины"}
        
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления из корзины")

@router.delete("/clear")
async def clear_cart(request: Request, db: Session = Depends(get_db)):
    """Очистить корзину"""
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        cart_service.clear_cart(session_id)
        
        return {"success": True, "message": "Корзина очищена"}
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail="Ошибка очистки корзины")
