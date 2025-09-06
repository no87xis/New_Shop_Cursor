"""
Роутер для проверки здоровья системы
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db import get_db, check_database_connection
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Базовая проверка здоровья системы
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0",
        "environment": settings.environment
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Детальная проверка здоровья системы
    """
    checks = {
        "database": await check_database_health(db),
        "whatsapp_relay": await check_whatsapp_relay_health(),
        "external_services": await check_external_services_health()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0",
        "environment": settings.environment
    }


async def check_database_health(db: Session) -> bool:
    """
    Проверка здоровья базы данных
    """
    try:
        # Простой запрос для проверки подключения
        db.execute("SELECT 1")
        logger.info("Database health check: OK")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_whatsapp_relay_health() -> bool:
    """
    Проверка здоровья WhatsApp Relay
    """
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.whatsapp_relay_url}/wa/health",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("ok", False) and data.get("clientReady", False)
        return False
    except Exception as e:
        logger.error(f"WhatsApp Relay health check failed: {e}")
        return False


async def check_external_services_health() -> bool:
    """
    Проверка здоровья внешних сервисов
    """
    try:
        # Здесь можно добавить проверки других внешних сервисов
        # Пока возвращаем True
        return True
    except Exception as e:
        logger.error(f"External services health check failed: {e}")
        return False