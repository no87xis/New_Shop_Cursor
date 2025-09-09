"""
API endpoints для загрузки фото товаров
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db import get_db
from app.models.product import Product
from app.services.image_upload_service import image_upload_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/products", tags=["product-photos"])

@router.post("/{product_id}/upload-photo")
async def upload_product_photo(
    product_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Загрузка фото товара
    
    Args:
        product_id: ID товара
        file: Загружаемый файл изображения
        alt_text: Альтернативный текст для изображения
        db: Сессия базы данных
        
    Returns:
        Информация о загруженном фото
    """
    try:
        # Проверяем существование товара
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Загружаем изображение
        photo_url, thumbnail_url = await image_upload_service.upload_product_image(
            file, product_id
        )
        
        # Обновляем товар в базе данных
        product.photo_url = photo_url
        product.photo_alt = alt_text or f"Фото товара {product.name}"
        product.has_photo = True
        product.photo_uploaded_at = datetime.now()
        product.updated_at = datetime.now()
        
        db.commit()
        db.refresh(product)
        
        logger.info(f"Photo uploaded for product {product_id}: {photo_url}")
        
        return {
            "success": True,
            "message": "Фото успешно загружено",
            "product_id": product_id,
            "photo_url": photo_url,
            "thumbnail_url": thumbnail_url,
            "alt_text": product.photo_alt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo for product {product_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки фото: {e}")

@router.delete("/{product_id}/delete-photo")
async def delete_product_photo(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Удаление фото товара
    
    Args:
        product_id: ID товара
        db: Сессия базы данных
        
    Returns:
        Результат удаления
    """
    try:
        # Проверяем существование товара
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        if not product.has_photo:
            return {
                "success": True,
                "message": "У товара нет фото для удаления"
            }
        
        # Удаляем файлы изображения
        deleted = image_upload_service.delete_product_image(product.photo_url)
        
        # Обновляем товар в базе данных
        product.photo_url = "/static/images/placeholder-product.jpg"
        product.photo_alt = "Изображение товара"
        product.has_photo = False
        product.photo_uploaded_at = None
        product.updated_at = datetime.now()
        
        db.commit()
        
        logger.info(f"Photo deleted for product {product_id}")
        
        return {
            "success": True,
            "message": "Фото успешно удалено",
            "product_id": product_id,
            "files_deleted": deleted
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting photo for product {product_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления фото: {e}")

@router.get("/{product_id}/photo")
async def get_product_photo(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение информации о фото товара
    
    Args:
        product_id: ID товара
        db: Сессия базы данных
        
    Returns:
        Информация о фото товара
    """
    try:
        # Проверяем существование товара
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        return {
            "product_id": product_id,
            "photo_url": product.get_photo_url(),
            "thumbnail_url": product.get_thumbnail_url(),
            "alt_text": product.photo_alt,
            "has_photo": product.has_photo,
            "photo_uploaded_at": product.photo_uploaded_at.isoformat() if product.photo_uploaded_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo info for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о фото: {e}")

@router.post("/{product_id}/set-placeholder")
async def set_placeholder_photo(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Установка placeholder изображения для товара
    
    Args:
        product_id: ID товара
        db: Сессия базы данных
        
    Returns:
        Результат установки placeholder
    """
    try:
        # Проверяем существование товара
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Удаляем старое фото если есть
        if product.has_photo:
            image_upload_service.delete_product_image(product.photo_url)
        
        # Устанавливаем placeholder
        product.photo_url = "/static/images/placeholder-product.jpg"
        product.photo_alt = "Изображение товара"
        product.has_photo = False
        product.photo_uploaded_at = None
        product.updated_at = datetime.now()
        
        db.commit()
        
        logger.info(f"Placeholder set for product {product_id}")
        
        return {
            "success": True,
            "message": "Placeholder изображение установлено",
            "product_id": product_id,
            "photo_url": product.photo_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting placeholder for product {product_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка установки placeholder: {e}")