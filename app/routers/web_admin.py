"""
Административные веб-страницы
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
import uuid
from datetime import datetime

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
    expected_date: str = Form(None),
    product_photo: UploadFile = File(None),
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
        
        # Обрабатываем загрузку фото
        photo_path = None
        if product_photo and product_photo.filename:
            # Создаем папку для загрузок если её нет
            upload_dir = "uploads/products"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Генерируем уникальное имя файла
            file_extension = os.path.splitext(product_photo.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            photo_path = os.path.join(upload_dir, unique_filename)
            
            # Сохраняем файл
            with open(photo_path, "wb") as buffer:
                content = await product_photo.read()
                buffer.write(content)
            
            logger.info(f"Photo uploaded: {photo_path}")
        
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
            availability_status=availability_status,
            expected_date=expected_date,
            photo_path=photo_path
        )
        
        product = product_service.create(product_data)
        
        return RedirectResponse(url="/admin/products", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания товара: {e}")


@router.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Форма редактирования товара
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.get(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        context = {
            "request": request,
            "product": product
        }
        
        return templates.TemplateResponse("admin/product_edit.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading edit product form: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки формы редактирования: {e}"
        })


@router.post("/admin/products/{product_id}/edit")
async def update_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(0),
    min_stock: int = Form(0),
    buy_price_eur: float = Form(None),
    sell_price_rub: float = Form(...),
    supplier_name: str = Form(""),
    availability_status: str = Form("IN_STOCK"),
    expected_date: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Обновление товара
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.get(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Проверяем, что товар с таким названием не существует (кроме текущего)
        existing_product = product_service.get_by_name(name)
        if existing_product and existing_product.id != product_id:
            raise HTTPException(status_code=400, detail="Товар с таким названием уже существует")
        
        # Обновляем товар
        from app.schemas.product import ProductUpdate
        product_data = ProductUpdate(
            name=name,
            description=description,
            quantity=quantity,
            min_stock=min_stock,
            buy_price_eur=buy_price_eur,
            sell_price_rub=sell_price_rub,
            supplier_name=supplier_name,
            availability_status=availability_status,
            expected_date=expected_date
        )
        
        updated_product = product_service.update(product_id, product_data)
        
        return RedirectResponse(url="/admin/products", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления товара: {e}")


@router.post("/admin/products/{product_id}/delete")
async def delete_product(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Удаление товара
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.get(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        product_service.delete(product_id)
        
        return RedirectResponse(url="/admin/products", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления товара: {e}")


@router.post("/admin/products/{product_id}/update-quantity")
async def update_product_quantity(
    request: Request,
    product_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Обновление количества товара
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        product = product_service.get(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Обновляем количество
        from app.schemas.product import ProductUpdate
        product_data = ProductUpdate(quantity=quantity)
        
        updated_product = product_service.update(product_id, product_data)
        
        return RedirectResponse(url="/admin/products", status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product quantity: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления количества: {e}")


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
    Аналитика и отчеты
    """
    try:
        if not check_admin_access(request):
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        product_service = ProductService(db)
        order_service = OrderService(db)
        shop_order_service = ShopOrderService(db)
        
        # Получаем статистику
        product_stats = product_service.get_statistics()
        order_stats = order_service.get_statistics()
        shop_order_stats = shop_order_service.get_statistics()
        
        # Популярные товары
        popular_products = product_service.get_popular_products(10)
        
        # Последние товары
        recent_products = product_service.get_recent_products(10)
        
        context = {
            "request": request,
            "product_stats": product_stats,
            "order_stats": order_stats,
            "shop_order_stats": shop_order_stats,
            "popular_products": popular_products,
            "recent_products": recent_products
        }
        
        return templates.TemplateResponse("admin/analytics.html", context)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading admin analytics: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки аналитики: {e}"
        })