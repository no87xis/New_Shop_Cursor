from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.shop_cart import ShopCart
from app.services.product_service import ProductService
from typing import List
import json

router = APIRouter()

def get_session_id(request: Request) -> str:
    """Получить или создать session_id"""
    session_id = request.session.get("session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
    return session_id

@router.post("/api/cart/add")
async def add_to_cart(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        product_id = body.get("product_id")
        quantity = body.get("quantity", 1)
        
        if not product_id:
            raise HTTPException(status_code=400, detail="product_id is required")
        
        product_service = ProductService(db)
        product = product_service.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Проверяем статус товара
        if product.availability_status not in ["IN_STOCK", "ON_ORDER"]:
            raise HTTPException(status_code=400, detail="Product not available")
        
        session_id = get_session_id(request)
        
        # Проверяем, есть ли уже такой товар в корзине
        existing_item = db.query(ShopCart).filter(
            ShopCart.session_id == session_id,
            ShopCart.product_id == product_id
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            cart_item = ShopCart(
                session_id=session_id,
                product_id=product_id,
                quantity=quantity,
                price=product.sell_price_rub
            )
            db.add(cart_item)
        
        db.commit()
        return {"status": "success", "message": "Товар добавлен в корзину"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/cart/count")
async def get_cart_count(request: Request, db: Session = Depends(get_db)):
    session_id = get_session_id(request)
    count = db.query(ShopCart).filter(ShopCart.session_id == session_id).count()
    return {"count": count}

@router.get("/api/cart")
async def get_cart(request: Request, db: Session = Depends(get_db)):
    session_id = get_session_id(request)
    cart_items = db.query(ShopCart).filter(ShopCart.session_id == session_id).all()
    
    product_service = ProductService(db)
    cart_data = []
    total = 0
    
    for item in cart_items:
        product = product_service.get_by_id(item.product_id)
        if product:
            item_total = item.quantity * item.price
            total += item_total
            cart_data.append({
                "id": item.id,
                "product_id": product.id,
                "name": product.name,
                "quantity": item.quantity,
                "price": item.price,
                "total": item_total,
                "photo_path": product.photo_path
            })
    
    return {"items": cart_data, "total": total}

@router.post("/api/cart/update")
async def update_cart_item(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        item_id = body.get("item_id")
        quantity = body.get("quantity")
        
        if not item_id or quantity is None:
            raise HTTPException(status_code=400, detail="item_id and quantity are required")
        
        session_id = get_session_id(request)
        cart_item = db.query(ShopCart).filter(
            ShopCart.id == item_id,
            ShopCart.session_id == session_id
        ).first()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        if quantity <= 0:
            db.delete(cart_item)
        else:
            cart_item.quantity = quantity
        
        db.commit()
        return {"status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/cart/remove")
async def remove_from_cart(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        item_id = body.get("item_id")
        
        if not item_id:
            raise HTTPException(status_code=400, detail="item_id is required")
        
        session_id = get_session_id(request)
        cart_item = db.query(ShopCart).filter(
            ShopCart.id == item_id,
            ShopCart.session_id == session_id
        ).first()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        db.delete(cart_item)
        db.commit()
        return {"status": "success"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/cart/clear")
async def clear_cart(request: Request, db: Session = Depends(get_db)):
    session_id = get_session_id(request)
    db.query(ShopCart).filter(ShopCart.session_id == session_id).delete()
    db.commit()
    return {"status": "success"}