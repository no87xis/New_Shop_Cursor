"""
Sirius Group V2 - Система управления складом и интернет-магазин с WhatsApp уведомлениями
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import logging
import os

from app.config import settings
from app.routers import shop_cart_api, shop_order_api, web_cart, web_checkout, web_order_success, web_shop
from app.routers import order_tracking_api, web_order_tracking, notifications_api, web_admin
from app.db import create_tables, check_database_connection

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Создание приложения FastAPI
app = FastAPI(
    title="Sirius Group V2",
    description="Система управления складом и интернет-магазин с WhatsApp уведомлениями",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
try:
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=settings.session_max_age,
        same_site="lax",
        https_only=False
    )
    logger.info("Session middleware added successfully")
except Exception as e:
    logger.error(f"Error adding session middleware: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
try:
    if os.path.exists("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
        logger.info("Static files mounted successfully")
    else:
        logger.warning("Static files directory not found")
except Exception as e:
    logger.error(f"Error mounting static files: {e}")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Подключение роутеров
try:
    # app.include_router(health.router)
    # app.include_router(web_public.router)
    app.include_router(web_shop.router)
    # app.include_router(shop_api.router)
    app.include_router(shop_cart_api.router)
    app.include_router(shop_order_api.router)
    app.include_router(web_cart.router)
    app.include_router(web_checkout.router)
    app.include_router(web_order_success.router)
    app.include_router(order_tracking_api.router)
    app.include_router(web_order_tracking.router)
    app.include_router(web_admin.router)
    # app.include_router(admin_api.router)
    # app.include_router(tracking.router)
    app.include_router(notifications_api.router)
    # app.include_router(web_notifications.router)
    # app.include_router(photo_upload_api.router)
    logger.info("All routers included successfully")
except Exception as e:
    logger.error(f"Error including routers: {e}")

# Обработчики ошибок
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Обработчик 404 ошибок"""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Страница не найдена",
        "status_code": 404
    }, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Обработчик 500 ошибок"""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Внутренняя ошибка сервера",
        "status_code": 500
    }, status_code=500)

# События приложения
@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    try:
        logger.info("Starting Sirius Group V2 application...")
        
        # Создание папки для логов
        os.makedirs("logs", exist_ok=True)
        
        # Создание папки для загрузок
        os.makedirs(settings.upload_dir, exist_ok=True)
        
        # Проверка подключения к базе данных
        if check_database_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
        
        # Создание таблиц
        create_tables()
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    logger.info("Shutting down Sirius Group V2 application...")

# Базовые роуты
@app.get("/")
async def root(request: Request):
    """Корневой роут"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error loading root page: {e}")
        return {"error": f"Template error: {e}"}

@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "ok",
        "version": "2.0",
        "environment": settings.environment,
        "debug": settings.debug
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )