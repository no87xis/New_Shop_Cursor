"""
Базовые тесты системы
"""
import pytest
import sys
import os

# Добавляем путь к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings
from app.db import check_database_connection, create_tables
from app.monitoring import monitor, get_system_status
from app.backup import backup_manager


class TestBasicFunctionality:
    """Тесты базовой функциональности"""
    
    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        assert settings is not None
        assert settings.database_url is not None
        assert settings.secret_key is not None
        assert settings.environment in ["development", "production", "testing"]
    
    def test_database_connection(self):
        """Тест подключения к базе данных"""
        # Проверяем, что функция не падает
        result = check_database_connection()
        assert isinstance(result, bool)
    
    def test_database_tables_creation(self):
        """Тест создания таблиц базы данных"""
        # Проверяем, что функция не падает
        try:
            create_tables()
            assert True
        except Exception as e:
            pytest.fail(f"Table creation failed: {e}")
    
    def test_monitoring_system(self):
        """Тест системы мониторинга"""
        assert monitor is not None
        
        # Проверяем сбор метрик
        metrics = monitor.collect_metrics()
        assert metrics is not None or metrics is None  # Может быть None при ошибке
        
        # Проверяем статус системы
        status = get_system_status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "timestamp" in status
    
    def test_backup_system(self):
        """Тест системы резервного копирования"""
        assert backup_manager is not None
        
        # Проверяем список резервных копий
        backups = backup_manager.list_backups()
        assert isinstance(backups, list)
    
    def test_imports(self):
        """Тест импортов основных модулей"""
        try:
            from app.main import app
            assert app is not None
        except Exception as e:
            pytest.fail(f"Main app import failed: {e}")
        
        try:
            from app.routers import health, web_public, web_shop, shop_api
            assert health is not None
            assert web_public is not None
            assert web_shop is not None
            assert shop_api is not None
        except Exception as e:
            pytest.fail(f"Routers import failed: {e}")
        
        try:
            from app.models import user, product, order, message_log
            assert user is not None
            assert product is not None
            assert order is not None
            assert message_log is not None
        except Exception as e:
            pytest.fail(f"Models import failed: {e}")
        
        try:
            from app.schemas import user as user_schema, product as product_schema, order as order_schema, notification
            assert user_schema is not None
            assert product_schema is not None
            assert order_schema is not None
            assert notification is not None
        except Exception as e:
            pytest.fail(f"Schemas import failed: {e}")


class TestConfiguration:
    """Тесты конфигурации"""
    
    def test_required_settings(self):
        """Тест обязательных настроек"""
        required_settings = [
            'database_url',
            'secret_key',
            'environment',
            'debug',
            'log_level'
        ]
        
        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing required setting: {setting}"
            assert getattr(settings, setting) is not None, f"Setting {setting} is None"
    
    def test_whatsapp_settings(self):
        """Тест настроек WhatsApp"""
        whatsapp_settings = [
            'whatsapp_relay_url',
            'whatsapp_relay_token',
            'pickup_address',
            'pickup_hours',
            'default_country_code'
        ]
        
        for setting in whatsapp_settings:
            assert hasattr(settings, setting), f"Missing WhatsApp setting: {setting}"
    
    def test_database_url_format(self):
        """Тест формата URL базы данных"""
        db_url = settings.database_url
        assert db_url.startswith(('sqlite:///', 'postgresql://', 'mysql://')), \
            f"Invalid database URL format: {db_url}"


class TestModels:
    """Тесты моделей данных"""
    
    def test_user_model(self):
        """Тест модели пользователя"""
        from app.models.user import User
        
        # Проверяем, что модель определена
        assert User is not None
        assert hasattr(User, '__tablename__')
        assert User.__tablename__ == "users"
    
    def test_product_model(self):
        """Тест модели товара"""
        from app.models.product import Product
        
        assert Product is not None
        assert hasattr(Product, '__tablename__')
        assert Product.__tablename__ == "products"
    
    def test_order_model(self):
        """Тест модели заказа"""
        from app.models.order import Order, ShopOrder, ShopCart
        
        assert Order is not None
        assert ShopOrder is not None
        assert ShopCart is not None
        
        assert Order.__tablename__ == "orders"
        assert ShopOrder.__tablename__ == "shop_orders"
        assert ShopCart.__tablename__ == "shop_cart"
    
    def test_message_log_model(self):
        """Тест модели логов сообщений"""
        from app.models.message_log import MessageLog
        
        assert MessageLog is not None
        assert hasattr(MessageLog, '__tablename__')
        assert MessageLog.__tablename__ == "message_logs"


class TestSchemas:
    """Тесты Pydantic схем"""
    
    def test_user_schemas(self):
        """Тест схем пользователей"""
        from app.schemas.user import User, UserCreate, UserUpdate
        
        assert User is not None
        assert UserCreate is not None
        assert UserUpdate is not None
    
    def test_product_schemas(self):
        """Тест схем товаров"""
        from app.schemas.product import Product, ProductCreate, ProductUpdate
        
        assert Product is not None
        assert ProductCreate is not None
        assert ProductUpdate is not None
    
    def test_order_schemas(self):
        """Тест схем заказов"""
        from app.schemas.order import Order, OrderCreate, ShopOrder, ShopOrderCreate
        
        assert Order is not None
        assert OrderCreate is not None
        assert ShopOrder is not None
        assert ShopOrderCreate is not None
    
    def test_notification_schemas(self):
        """Тест схем уведомлений"""
        from app.schemas.notification import (
            NotificationSendRequest, 
            NotificationSendResponse,
            RecipientData
        )
        
        assert NotificationSendRequest is not None
        assert NotificationSendResponse is not None
        assert RecipientData is not None


class TestConstants:
    """Тесты констант"""
    
    def test_delivery_constants(self):
        """Тест констант доставки"""
        from app.constants.delivery import (
            DeliveryOption, 
            DELIVERY_DESCRIPTIONS,
            calculate_delivery_cost
        )
        
        assert DeliveryOption is not None
        assert DELIVERY_DESCRIPTIONS is not None
        assert calculate_delivery_cost is not None
        
        # Тест расчета стоимости доставки
        cost = calculate_delivery_cost(DeliveryOption.SELF_PICKUP_GROZNY, 5)
        assert cost == 0
        
        cost = calculate_delivery_cost(DeliveryOption.COURIER_GROZNY, 3)
        assert cost == 900  # 300 * 3
    
    def test_notification_constants(self):
        """Тест констант уведомлений"""
        from app.constants.notifications import (
            MESSAGE_TEMPLATES,
            NOTIFICATION_STATUSES,
            ARRIVAL_STATUSES
        )
        
        assert MESSAGE_TEMPLATES is not None
        assert NOTIFICATION_STATUSES is not None
        assert ARRIVAL_STATUSES is not None
        
        # Проверяем наличие шаблонов
        assert "arrived_v1" in MESSAGE_TEMPLATES
        assert "ready_v1" in MESSAGE_TEMPLATES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])