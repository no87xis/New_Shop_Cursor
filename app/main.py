from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Создание папки для логов
os.makedirs("logs", exist_ok=True)

app = FastAPI(
    title="Sirius Shop",
    description="Система управления складом и интернет-магазином",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Загруженные файлы
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    logger.info("Uploads directory mounted successfully")
else:
    os.makedirs("uploads", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    logger.info("Uploads directory created and mounted")

# Подключение роутеров
from app.routers import web_admin, web_shop, shop_api

app.include_router(web_admin.router)
app.include_router(web_shop.router)
app.include_router(shop_api.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Sirius Shop is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)