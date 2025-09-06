"""
Конфигурация приложения Sirius Group V2
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Database
    database_url: str = Field(default="sqlite:///./sirius.db", description="URL базы данных")
    
    # Security
    secret_key: str = Field(default="your-secret-key-32-characters-long-2024", description="Секретный ключ")
    session_max_age: int = Field(default=86400, description="Время жизни сессии в секундах")
    
    # External Services
    telegram_bot_token: Optional[str] = Field(default=None, description="Токен Telegram бота")
    telegram_chat_id: Optional[str] = Field(default=None, description="ID чата Telegram")
    
    # Email Settings
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP хост")
    smtp_port: int = Field(default=587, description="SMTP порт")
    smtp_username: Optional[str] = Field(default=None, description="SMTP пользователь")
    smtp_password: Optional[str] = Field(default=None, description="SMTP пароль")
    smtp_use_tls: bool = Field(default=True, description="Использовать TLS")
    
    # Application Settings
    environment: str = Field(default="development", description="Окружение")
    debug: bool = Field(default=True, description="Режим отладки")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    
    # Cache
    redis_url: str = Field(default="redis://localhost:6379/0", description="URL Redis")
    
    # File Upload
    max_file_size: int = Field(default=10485760, description="Максимальный размер файла")
    upload_dir: str = Field(default="uploads", description="Папка загрузок")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Включить ограничение скорости")
    rate_limit_requests: int = Field(default=100, description="Количество запросов")
    rate_limit_window: int = Field(default=60, description="Окно времени в секундах")
    
    # Monitoring
    prometheus_enabled: bool = Field(default=True, description="Включить Prometheus")
    health_check_interval: int = Field(default=30, description="Интервал проверки здоровья")
    
    # Development
    reload: bool = Field(default=True, description="Автоперезагрузка")
    host: str = Field(default="127.0.0.1", description="Хост")
    port: int = Field(default=8000, description="Порт")
    
    # WhatsApp Relay - НОВОЕ
    whatsapp_relay_url: str = Field(default="http://localhost:3000", description="URL WhatsApp Relay")
    whatsapp_relay_token: str = Field(default="your-wa-relay-token", description="Токен WhatsApp Relay")
    pickup_address: str = Field(default="Наш склад, ул. Примерная, 123", description="Адрес пункта выдачи")
    pickup_hours: str = Field(default="Пн-Пт: 10:00-19:00, Сб: 10:00-16:00", description="Часы работы")
    default_country_code: str = Field(default="BY", description="Код страны по умолчанию")
    
    # WhatsApp Settings - НОВОЕ
    whatsapp_send_delay_min_ms: int = Field(default=900, description="Минимальная задержка отправки")
    whatsapp_send_delay_max_ms: int = Field(default=1700, description="Максимальная задержка отправки")
    whatsapp_rate_limit_per_min: int = Field(default=45, description="Лимит сообщений в минуту")
    whatsapp_session_path: str = Field(default="./.wwebjs_auth", description="Путь к сессии WhatsApp")
    
    # Notification Templates - НОВОЕ
    notification_template_arrived: str = Field(default="arrived_v1", description="Шаблон уведомления о прибытии")
    notification_template_ready: str = Field(default="ready_v1", description="Шаблон уведомления о готовности")
    notification_template_shipped: str = Field(default="shipped_v1", description="Шаблон уведомления об отправке")
    
    # Phone Validation - НОВОЕ
    phone_validation_enabled: bool = Field(default=True, description="Включить валидацию телефонов")
    phone_default_country: str = Field(default="BY", description="Страна по умолчанию для телефонов")
    phone_allowed_countries: str = Field(default="BY,RU,UA", description="Разрешенные страны")
    
    # Message Logging - НОВОЕ
    message_log_enabled: bool = Field(default=True, description="Включить логирование сообщений")
    message_log_retention_days: int = Field(default=30, description="Дни хранения логов")
    message_log_cleanup_interval: int = Field(default=24, description="Интервал очистки логов")
    
    # Batch Processing - НОВОЕ
    batch_size_max: int = Field(default=50, description="Максимальный размер батча")
    batch_delay_ms: int = Field(default=1000, description="Задержка между батчами")
    batch_retry_attempts: int = Field(default=3, description="Количество попыток повтора")
    batch_retry_delay_ms: int = Field(default=5000, description="Задержка повтора")
    
    # Security - НОВОЕ
    whatsapp_auth_required: bool = Field(default=True, description="Требовать авторизацию WhatsApp")
    whatsapp_ip_whitelist: str = Field(default="", description="Белый список IP")
    whatsapp_rate_limit_per_ip: int = Field(default=10, description="Лимит запросов с IP")
    whatsapp_rate_limit_window: int = Field(default=60, description="Окно времени для IP")
    
    # Monitoring - НОВОЕ
    whatsapp_monitoring_enabled: bool = Field(default=True, description="Включить мониторинг WhatsApp")
    whatsapp_metrics_enabled: bool = Field(default=True, description="Включить метрики WhatsApp")
    whatsapp_alerts_enabled: bool = Field(default=True, description="Включить алерты WhatsApp")
    whatsapp_alert_email: str = Field(default="admin@example.com", description="Email для алертов")
    
    # Testing - НОВОЕ
    whatsapp_test_mode: bool = Field(default=False, description="Тестовый режим WhatsApp")
    whatsapp_test_phone: str = Field(default="+375291234567", description="Тестовый телефон")
    whatsapp_dry_run_enabled: bool = Field(default=True, description="Включить dry-run режим")
    
    # Development Tools - НОВОЕ
    whatsapp_debug_enabled: bool = Field(default=False, description="Включить отладку WhatsApp")
    whatsapp_verbose_logging: bool = Field(default=False, description="Подробное логирование WhatsApp")
    whatsapp_save_messages: bool = Field(default=True, description="Сохранять сообщения")
    whatsapp_save_qr_codes: bool = Field(default=True, description="Сохранять QR коды")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()