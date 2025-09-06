"""
Публичные веб-страницы
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging

from app.db import get_db
from app.models.product import Product
from app.models.order import Order, ShopOrder

logger = logging.getLogger(__name__)
router = APIRouter()

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """
    Главная страница
    """
    try:
        # Получаем статистику для главной страницы
        total_products = db.query(Product).count()
        total_orders = db.query(Order).count()
        total_shop_orders = db.query(ShopOrder).count()
        
        # Получаем последние товары
        recent_products = db.query(Product).order_by(Product.created_at.desc()).limit(6).all()
        
        context = {
            "request": request,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_shop_orders": total_shop_orders,
            "recent_products": recent_products
        }
        
        return templates.TemplateResponse("index.html", context)
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки главной страницы: {e}"
        })


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """
    Страница "О нас"
    """
    try:
        return templates.TemplateResponse("about.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading about page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки страницы: {e}"
        })


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """
    Страница контактов
    """
    try:
        return templates.TemplateResponse("contact.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading contact page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки страницы: {e}"
        })