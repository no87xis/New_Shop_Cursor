"""
Сервис для генерации QR-кодов
"""
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import uuid
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class QRCodeService:
    """Сервис для работы с QR-кодами"""
    
    def __init__(self):
        self.qr_factory = qrcode.image.svg.SvgPathImage
    
    def generate_qr_code(self, data: str, size: int = 200) -> str:
        """
        Генерация QR-кода в формате base64
        
        Args:
            data: Данные для кодирования
            size: Размер QR-кода в пикселях
            
        Returns:
            Base64 строка с SVG изображением
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Создаем SVG изображение
            img = qr.make_image(image_factory=self.qr_factory)
            
            # Конвертируем в base64
            buffer = BytesIO()
            img.save(buffer)
            buffer.seek(0)
            
            svg_data = buffer.getvalue().decode('utf-8')
            base64_data = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
            
            return f"data:image/svg+xml;base64,{base64_data}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return None
    
    def generate_order_qr_code(self, order_code: str, order_id: int) -> Dict[str, Any]:
        """
        Генерация QR-кода для заказа
        
        Args:
            order_code: Код заказа
            order_id: ID заказа
            
        Returns:
            Словарь с данными QR-кода
        """
        try:
            # Создаем уникальный токен для заказа
            qr_token = str(uuid.uuid4())
            
            # Данные для QR-кода
            qr_data = {
                "order_code": order_code,
                "order_id": order_id,
                "token": qr_token,
                "timestamp": datetime.now().isoformat(),
                "type": "order_tracking"
            }
            
            # Генерируем QR-код
            qr_code_data = f"order:{order_code}:{qr_token}"
            qr_code_base64 = self.generate_qr_code(qr_code_data)
            
            return {
                "qr_code": qr_code_base64,
                "qr_token": qr_token,
                "qr_data": qr_data,
                "order_code": order_code,
                "order_id": order_id
            }
            
        except Exception as e:
            logger.error(f"Error generating order QR code: {e}")
            return None
    
    def generate_shop_order_qr_code(self, order_code: str, order_id: int) -> Dict[str, Any]:
        """
        Генерация QR-кода для заказа магазина
        
        Args:
            order_code: Код заказа
            order_id: ID заказа
            
        Returns:
            Словарь с данными QR-кода
        """
        try:
            # Создаем уникальный токен для заказа
            qr_token = str(uuid.uuid4())
            
            # Данные для QR-кода
            qr_data = {
                "order_code": order_code,
                "order_id": order_id,
                "token": qr_token,
                "timestamp": datetime.now().isoformat(),
                "type": "shop_order_tracking"
            }
            
            # Генерируем QR-код
            qr_code_data = f"shop_order:{order_code}:{qr_token}"
            qr_code_base64 = self.generate_qr_code(qr_code_data)
            
            return {
                "qr_code": qr_code_base64,
                "qr_token": qr_token,
                "qr_data": qr_data,
                "order_code": order_code,
                "order_id": order_id
            }
            
        except Exception as e:
            logger.error(f"Error generating shop order QR code: {e}")
            return None
    
    def generate_product_qr_code(self, product_id: int, product_name: str) -> Dict[str, Any]:
        """
        Генерация QR-кода для товара
        
        Args:
            product_id: ID товара
            product_name: Название товара
            
        Returns:
            Словарь с данными QR-кода
        """
        try:
            # Создаем уникальный токен для товара
            qr_token = str(uuid.uuid4())
            
            # Данные для QR-кода
            qr_data = {
                "product_id": product_id,
                "product_name": product_name,
                "token": qr_token,
                "timestamp": datetime.now().isoformat(),
                "type": "product_info"
            }
            
            # Генерируем QR-код
            qr_code_data = f"product:{product_id}:{qr_token}"
            qr_code_base64 = self.generate_qr_code(qr_code_data)
            
            return {
                "qr_code": qr_code_base64,
                "qr_token": qr_token,
                "qr_data": qr_data,
                "product_id": product_id,
                "product_name": product_name
            }
            
        except Exception as e:
            logger.error(f"Error generating product QR code: {e}")
            return None
    
    def parse_qr_code_data(self, qr_data: str) -> Optional[Dict[str, Any]]:
        """
        Парсинг данных из QR-кода
        
        Args:
            qr_data: Данные из QR-кода
            
        Returns:
            Распарсенные данные или None
        """
        try:
            parts = qr_data.split(':')
            if len(parts) < 3:
                return None
            
            qr_type = parts[0]
            identifier = parts[1]
            token = parts[2]
            
            return {
                "type": qr_type,
                "identifier": identifier,
                "token": token,
                "raw_data": qr_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing QR code data: {e}")
            return None
    
    def validate_qr_token(self, qr_data: str, expected_type: str = None) -> bool:
        """
        Валидация токена QR-кода
        
        Args:
            qr_data: Данные из QR-кода
            expected_type: Ожидаемый тип QR-кода
            
        Returns:
            True если токен валиден
        """
        try:
            parsed_data = self.parse_qr_code_data(qr_data)
            if not parsed_data:
                return False
            
            if expected_type and parsed_data.get("type") != expected_type:
                return False
            
            # Здесь можно добавить дополнительную валидацию токена
            # Например, проверку в базе данных или проверку времени создания
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating QR token: {e}")
            return False
    
    def generate_tracking_url(self, order_code: str, qr_token: str) -> str:
        """
        Генерация URL для отслеживания заказа
        
        Args:
            order_code: Код заказа
            qr_token: Токен QR-кода
            
        Returns:
            URL для отслеживания
        """
        try:
            # Здесь должен быть базовый URL приложения
            base_url = "http://localhost:8000"  # В продакшене это должно быть из настроек
            
            return f"{base_url}/track/{order_code}?token={qr_token}"
            
        except Exception as e:
            logger.error(f"Error generating tracking URL: {e}")
            return None


# Глобальный экземпляр сервиса
qr_service = QRCodeService()