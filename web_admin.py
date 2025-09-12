"""
from sqlalchemy import func
Административные веб-страницы
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db import get_db
from app.models.product import Product
from app.models.order import Order, ShopOrder
from app.models.user import User
from app.services.product_service import ProductService
from app.services.order_service import OrderService, ShopOrderService

logger = logging.getLogger(__name__)
router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")


def check_admin_access(request: Request):
    """Проверка прав администратора"""
    # Здесь должна быть проверка авторизации
    # Пока возвращаем True для разработки
    return True


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Главная панель администратора
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Получаем статистику
        product_service = ProductService(db)
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        product_stats = product_service.get_statistics()
        order_stats = order_service.get_statistics()
        shop_order_stats = shop_order_service.get_statistics()
        
        # Последние заказы
        recent_orders = db.query(ShopOrder).order_by(ShopOrder.created_at.desc()).limit(5).all()
        
        # Товары с низким остатком
        low_stock_products = product_service.get_low_stock_products()
        
        context = {
            "request": request,
            "product_stats": product_stats,
            "order_stats": order_stats,
            "shop_order_stats": shop_order_stats,
            "recent_orders": recent_orders,
            "low_stock_products": low_stock_products
        }
        
        return templates.TemplateResponse("admin/dashboard.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки панели администратора: {e}"
        })


@router.get("/admin/products", response_class=HTMLResponse)
async def admin_products(
    request: Request, 
    db: Session = Depends(get_db),
    page: int = 1,
    status: str = None,
    search: str = None
):
    """
    Управление товарами
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        
        # Фильтры
        filters = {}
        if status:
            filters["availability_status"] = status
        
        # Поиск
        if search:
            products = product_service.search_products(search)
        else:
            products = product_service.get_multi(skip=(page-1)*20, limit=20, filters=filters)
        
        # Статистика
        stats = product_service.get_statistics()
        
        context = {
            "request": request,
            "products": products,
            "stats": stats,
            "current_page": page,
            "current_status": status,
            "search_term": search
        }
        
        return templates.TemplateResponse("admin/products.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading admin products: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки товаров: {e}"
        })


@router.post("/admin/products")
async def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(0),
    min_stock: int = Form(0),
    buy_price_eur: float = Form(None),
    sell_price_rub: float = Form(...),
    supplier_name: str = Form(""),
    availability_status: str = Form("IN_STOCK"),
    db: Session = Depends(get_db)
):
    """
    Создание нового товара
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        
        # Проверяем, что товар с таким названием не существует
        existing_product = product_service.get_by_name(name)
        if existing_product:
            raise HTTPException(status_code=400, detail="Товар с таким названием уже существует")
        
        # Создаем товар
        from app.schemas.product import ProductCreate
        product_data = ProductCreate(
            name=name,
            description=description,
            quantity=quantity,
            min_stock=min_stock,
            buy_price_eur=buy_price_eur,
            sell_price_rub=sell_price_rub,
            supplier_name=supplier_name,
            availability_status=availability_status
        )
        
        product = product_service.create(product_data)
        
        return RedirectResponse(url="/admin/products", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания товара: {e}")


@router.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    status: str = None,
    search: str = None
):
    """
    Управление заказами
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        
        # Фильтры
        filters = {}
        if status:
            filters["status"] = status
        
        # Поиск
        if search:
            # Поиск по коду заказа или телефону
            orders = db.query(ShopOrder).filter(
                (ShopOrder.order_code.ilike(f"%{search}%")) |
                (ShopOrder.customer_phone.ilike(f"%{search}%")) |
                (ShopOrder.customer_name.ilike(f"%{search}%"))
            ).all()
        else:
            orders = shop_order_service.get_multi(skip=(page-1)*20, limit=20, filters=filters)
        
        # Статистика
        stats = shop_order_service.get_statistics()
        
        context = {
            "request": request,
            "orders": orders,
            "stats": stats,
            "current_page": page,
            "current_status": status,
            "search_term": search
        }
        
        return templates.TemplateResponse("admin/orders.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading admin orders: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки заказов: {e}"
        })


@router.post("/admin/orders/{order_id}/status")
async def update_order_status(
    request: Request,
    order_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Обновление статуса заказа
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        shop_order_service = ShopOrderService(db)
        order = shop_order_service.update_status(order_id, status)
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        return RedirectResponse(url="/admin/orders", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления статуса заказа: {e}")


@router.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    """
    Аналитика и отчеты - упрощенная версия
    """
    try:
        # Получаем статистику простыми запросами
        total_orders = db.query(ShopOrder).count()
        
        # Считаем общую сумму вручную
        orders = db.query(ShopOrder).all()
        total_amount = sum(float(order.total_amount) for order in orders if order.total_amount)
        
        total_products = db.query(Product).count()
        total_cart_items = db.query(ShopCart).count()
        
        # Последние заказы
        recent_orders = db.query(ShopOrder).order_by(ShopOrder.created_at.desc()).limit(10).all()
        
        context = {
            "request": request,
            "total_orders": total_orders,
            "total_amount": total_amount,
            "total_products": total_products,
            "total_cart_items": total_cart_items,
            "recent_orders": recent_orders
        }
        
        return templates.TemplateResponse("admin/analytics.html", context)
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        # Fallback значения
        context = {
            "request": request,
            "total_orders": 0,
            "total_amount": 0.0,
            "total_products": 0,
            "total_cart_items": 0,
            "recent_orders": []
        }
        return templates.TemplateResponse("admin/analytics.html", context)
