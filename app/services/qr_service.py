"""
Сервис для генерации QR-кодов заказов
"""
import qrcode
import qrcode.image.svg
import uuid
import os
from typing import Optional
from app.models.shop_order import ShopOrder
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class QRCodeService:
    """Сервис для работы с QR-кодами заказов"""
    
    @staticmethod
    def generate_qr_token() -> str:
        """Генерирует уникальный токен для QR-кода"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_qr_code(qr_token: str, order_code: str) -> str:
        """
        Генерирует QR-код и сохраняет его как SVG файл
        Возвращает путь к файлу QR-кода
        """
        try:
            # Создаем директорию для QR-кодов если её нет
            qr_dir = "static/qr_codes"
            os.makedirs(qr_dir, exist_ok=True)
            
            # URL для отслеживания заказа
            tracking_url = f"http://185.239.50.157:8000/shop/o/{qr_token}"
            
            # Создаем QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(tracking_url)
            qr.make(fit=True)
            
            # Создаем SVG изображение
            img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
            
            # Сохраняем файл
            qr_filename = f"order_{order_code}_{qr_token[:8]}.svg"
            qr_path = os.path.join(qr_dir, qr_filename)
            
            with open(qr_path, 'wb') as f:
                img.save(f)
            
            logger.info(f"QR-код создан: {qr_path}")
            return f"/static/qr_codes/{qr_filename}"
            
        except Exception as e:
            logger.error(f"Ошибка создания QR-кода: {e}")
            return None
    
    @staticmethod
    def update_order_qr(db: Session, order_id: int, qr_token: str, qr_code_path: str) -> bool:
        """Обновляет заказ QR-кодом"""
        try:
            order = db.query(ShopOrder).filter(ShopOrder.id == order_id).first()
            if order:
                order.qr_token = qr_token
                order.qr_code_path = qr_code_path
                db.commit()
                logger.info(f"QR-код добавлен к заказу {order.order_code}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка обновления заказа QR-кодом: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_order_by_qr_token(db: Session, qr_token: str) -> Optional[ShopOrder]:
        """Получает заказ по QR-токену"""
        try:
            return db.query(ShopOrder).filter(ShopOrder.qr_token == qr_token).first()
        except Exception as e:
            logger.error(f"Ошибка поиска заказа по QR-токену: {e}")
            return None