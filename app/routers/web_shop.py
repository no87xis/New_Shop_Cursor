"""
Веб-страницы магазина
"""
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db import get_db
from app.models.product import Product
from app.models.order import ShopOrder, ShopCart
from app.schemas.order import ShopOrderCreate, ShopCartSummary
from app.constants.delivery import DeliveryOption, calculate_delivery_cost, get_delivery_description

logger = logging.getLogger(__name__)
router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")


def get_session_id(request: Request) -> str:
    """
    Получение ID сессии из запроса
    """
    session_id = request.session.get("session_id")
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
    return session_id


@router.get("/shop/", response_class=HTMLResponse)
async def shop_catalog(request: Request, db: Session = Depends(get_db)):
    """
    Каталог товаров магазина
    """
    try:
        # Получаем товары с фильтрацией
        products = db.query(Product).filter(Product.quantity > 0).all()
        
        # Получаем количество товаров в корзине
        session_id = get_session_id(request)
        cart_count = db.query(ShopCart).filter(ShopCart.session_id == session_id).count()
        
        context = {
            "request": request,
            "products": products,
            "cart_count": cart_count
        }
        
        return templates.TemplateResponse("shop/catalog.html", context)
    except Exception as e:
        logger.error(f"Error loading shop catalog: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки каталога: {e}"
        })


@router.get("/shop/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    """
    Страница товара
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Получаем количество товаров в корзине
        session_id = get_session_id(request)
        cart_count = db.query(ShopCart).filter(ShopCart.session_id == session_id).count()
        
        context = {
            "request": request,
            "product": product,
            "cart_count": cart_count
        }
        
        return templates.TemplateResponse("shop/product_detail.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading product detail: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки товара: {e}"
        })


@router.get("/shop/cart", response_class=HTMLResponse)
async def shop_cart(request: Request, db: Session = Depends(get_db)):
    """
    Корзина магазина
    """
    try:
        session_id = get_session_id(request)
        
        # Получаем товары в корзине
        cart_items = db.query(ShopCart).filter(ShopCart.session_id == session_id).all()
        
        # Подготавливаем данные для шаблона
        cart_data = []
        total_amount = 0
        
        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                item_total = float(product.sell_price_rub or 0) * item.quantity
                cart_data.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price_rub": float(product.sell_price_rub or 0),
                    "total_price": item_total
                })
                total_amount += item_total
        
        context = {
            "request": request,
            "cart": {
                "items": cart_data,
                "total_items": len(cart_data),
                "total_amount": total_amount
            }
        }
        
        return templates.TemplateResponse("shop/cart.html", context)
    except Exception as e:
        logger.error(f"Error loading cart: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки корзины: {e}"
        })


@router.get("/shop/checkout", response_class=HTMLResponse)
async def shop_checkout(request: Request, db: Session = Depends(get_db)):
    """
    Оформление заказа
    """
    try:
        session_id = get_session_id(request)
        
        # Получаем товары в корзине
        cart_items = db.query(ShopCart).filter(ShopCart.session_id == session_id).all()
        
        if not cart_items:
            return RedirectResponse(url="/shop/cart", status_code=302)
        
        # Подготавливаем данные для шаблона
        cart_data = []
        total_amount = 0
        
        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                item_total = float(product.sell_price_rub or 0) * item.quantity
                cart_data.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": item.quantity,
                    "unit_price_rub": float(product.sell_price_rub or 0),
                    "total_price": item_total
                })
                total_amount += item_total
        
        # Варианты доставки
        delivery_options = [
            {"value": option.value, "description": get_delivery_description(option)}
            for option in DeliveryOption
        ]
        
        context = {
            "request": request,
            "cart": {
                "items": cart_data,
                "total_items": len(cart_data),
                "total_amount": total_amount
            },
            "delivery_options": delivery_options
        }
        
        return templates.TemplateResponse("shop/checkout.html", context)
    except Exception as e:
        logger.error(f"Error loading checkout: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки оформления заказа: {e}"
        })


@router.post("/shop/checkout")
async def process_checkout(
    request: Request,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    customer_city: Optional[str] = Form(None),
    delivery_option: str = Form(...),
    delivery_city_other: Optional[str] = Form(None),
    whatsapp_phone: Optional[str] = Form(None),
    consent_whatsapp: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Обработка оформления заказа
    """
    try:
        session_id = get_session_id(request)
        
        # Получаем товары в корзине
        cart_items = db.query(ShopCart).filter(ShopCart.session_id == session_id).all()
        
        if not cart_items:
            raise HTTPException(status_code=400, detail="Корзина пуста")
        
        # Создаем заказы для каждого товара в корзине
        created_orders = []
        
        for item in cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue
            
            # Генерируем код заказа
            import uuid
            order_code = f"A-{str(uuid.uuid4())[:6].upper()}"
            
            # Рассчитываем стоимость доставки
            delivery_cost = calculate_delivery_cost(DeliveryOption(delivery_option), item.quantity)
            
            # Создаем заказ
            order = ShopOrder(
                order_code=order_code,
                order_code_last4=order_code[-4:],
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_city=customer_city,
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                unit_price_rub=product.sell_price_rub,
                total_amount=float(product.sell_price_rub or 0) * item.quantity + delivery_cost,
                delivery_option=delivery_option,
                delivery_city_other=delivery_city_other,
                delivery_cost_rub=delivery_cost,
                whatsapp_phone=whatsapp_phone,
                consent_whatsapp=consent_whatsapp
            )
            
            db.add(order)
            created_orders.append(order)
        
        # Очищаем корзину
        db.query(ShopCart).filter(ShopCart.session_id == session_id).delete()
        
        # Сохраняем изменения
        db.commit()
        
        # Перенаправляем на страницу успеха
        return RedirectResponse(url=f"/shop/order-success?orders={','.join([o.order_code for o in created_orders])}", status_code=302)
        
    except Exception as e:
        logger.error(f"Error processing checkout: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка оформления заказа: {e}")


@router.get("/shop/order-success", response_class=HTMLResponse)
async def order_success(request: Request, orders: str = None):
    """
    Страница успешного оформления заказа
    """
    try:
        order_codes = orders.split(",") if orders else []
        
        context = {
            "request": request,
            "order_codes": order_codes
        }
        
        return templates.TemplateResponse("shop/order_success.html", context)
    except Exception as e:
        logger.error(f"Error loading order success page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки страницы: {e}"
        })