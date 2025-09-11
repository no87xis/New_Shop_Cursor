"""
Сервис для загрузки и обработки изображений товаров
"""
import os
import uuid
import shutil
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImageUploadService:
    """Сервис для загрузки изображений товаров"""
    
    def __init__(self, upload_dir: str = "uploads/products"):
        self.upload_dir = upload_dir
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        self.max_size = (800, 600)  # Максимальный размер изображения
        self.thumbnail_size = (200, 150)  # Размер миниатюры
        
        # Создаем директории
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(f"{self.upload_dir}/thumbnails", exist_ok=True)
    
    async def upload_product_image(
        self, 
        file: UploadFile, 
        product_id: int
    ) -> Tuple[str, str]:
        """
        Загружает и обрабатывает изображение товара
        
        Args:
            file: Загружаемый файл
            product_id: ID товара
            
        Returns:
            Tuple[photo_url, thumbnail_url]
        """
        try:
            # Проверяем расширение файла
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(self.allowed_extensions)}"
                )
            
            # Генерируем уникальное имя файла
            file_id = str(uuid.uuid4())
            filename = f"product_{product_id}_{file_id}{file_extension}"
            thumbnail_filename = f"product_{product_id}_{file_id}_thumb{file_extension}"
            
            # Пути для сохранения
            file_path = os.path.join(self.upload_dir, filename)
            thumbnail_path = os.path.join(self.upload_dir, "thumbnails", thumbnail_filename)
            
            # Сохраняем файл
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Обрабатываем изображение
            await self._process_image(file_path, thumbnail_path)
            
            # Возвращаем URL для доступа к файлам
            photo_url = f"/static/uploads/products/{filename}"
            thumbnail_url = f"/static/uploads/products/thumbnails/{thumbnail_filename}"
            
            logger.info(f"Image uploaded for product {product_id}: {photo_url}")
            
            return photo_url, thumbnail_url
            
        except Exception as e:
            logger.error(f"Error uploading image for product {product_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Ошибка загрузки изображения: {e}")
    
    async def _process_image(self, image_path: str, thumbnail_path: str):
        """
        Обрабатывает изображение: изменяет размер и создает миниатюру
        
        Args:
            image_path: Путь к исходному изображению
            thumbnail_path: Путь для сохранения миниатюры
        """
        try:
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Изменяем размер основного изображения
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                img.save(image_path, 'JPEG', quality=85, optimize=True)
                
                # Создаем миниатюру
                with Image.open(image_path) as thumb_img:
                    thumb_img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                    thumb_img.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
                    
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            raise
    
    def delete_product_image(self, photo_url: str) -> bool:
        """
        Удаляет изображение товара
        
        Args:
            photo_url: URL изображения
            
        Returns:
            True если удаление успешно
        """
        try:
            if not photo_url or photo_url.startswith('/static/uploads/products/'):
                return False
            
            # Извлекаем имя файла из URL
            filename = os.path.basename(photo_url)
            file_path = os.path.join(self.upload_dir, filename)
            
            # Удаляем основное изображение
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Удаляем миниатюру
            thumbnail_path = os.path.join(self.upload_dir, "thumbnails", filename)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            
            logger.info(f"Deleted image: {photo_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting image {photo_url}: {e}")
            return False
    
    def get_placeholder_image(self) -> str:
        """
        Возвращает URL placeholder изображения
        
        Returns:
            URL placeholder изображения
        """
        return "/static/images/placeholder-product.jpg"

# Глобальный экземпляр сервиса
image_upload_service = ImageUploadService()