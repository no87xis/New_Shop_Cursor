# 🏗️ ПЛАН НАДЕЖНОЙ АРХИТЕКТУРЫ SIRIUS GROUP V2
## Как правильно проектировать систему с WhatsApp уведомлениями, чтобы избежать падений и ошибок

---

## 🎯 ПРИНЦИПЫ НАДЕЖНОЙ АРХИТЕКТУРЫ

### **1. Модульность и разделение ответственности**
- Каждый модуль отвечает за одну задачу
- Четкие границы между компонентами
- Минимальные зависимости между модулями
- Возможность независимого тестирования
- **Изоляция WhatsApp Relay как отдельного микросервиса** - НОВОЕ

### **2. Обработка ошибок на всех уровнях**
- Graceful degradation (плавная деградация)
- Fallback механизмы
- Детальное логирование
- Мониторинг состояния системы
- **Обработка ошибок WhatsApp отправки** - НОВОЕ

### **3. Простота и читаемость кода**
- KISS принцип (Keep It Simple, Stupid)
- Понятные названия переменных и функций
- Комментарии для сложной логики
- Единый стиль кодирования

### **4. Тестируемость**
- Unit тесты для каждого компонента
- Integration тесты для API
- E2E тесты для критических сценариев
- Автоматическое тестирование при деплое
- **Тесты для WhatsApp уведомлений** - НОВОЕ

---

## 🏛️ РЕКОМЕНДУЕМАЯ АРХИТЕКТУРА

### **Слой 1: Презентационный (Presentation Layer)**
```
📁 templates/
├── base.html              # Базовый шаблон
├── components/            # Переиспользуемые компоненты
│   ├── navbar.html
│   ├── footer.html
│   ├── modal.html
│   └── notification_modal.html  # НОВОЕ: Модалка уведомлений
├── pages/                 # Страницы приложения
│   ├── shop/
│   ├── admin/
│   │   └── notifications/  # НОВОЕ: Страницы уведомлений
│   └── auth/
└── errors/                # Страницы ошибок
    ├── 404.html
    ├── 500.html
    └── maintenance.html
```

### **Слой 2: Контроллеры (Controllers/Routers)**
```
📁 routers/
├── __init__.py
├── api/                   # API эндпоинты
│   ├── auth.py
│   ├── products.py
│   ├── orders.py
│   ├── analytics.py
│   └── notifications.py   # НОВОЕ: API уведомлений
├── web/                   # Web страницы
│   ├── shop.py
│   ├── admin.py
│   ├── auth.py
│   └── admin_notifications.py  # НОВОЕ: Админ уведомления
└── health.py              # Health checks
```

### **Слой 3: Сервисы (Business Logic)**
```
📁 services/
├── __init__.py
├── base/                  # Базовые сервисы
│   ├── base_service.py
│   └── cache_service.py
├── domain/                # Доменные сервисы
│   ├── product_service.py
│   ├── order_service.py
│   ├── cart_service.py
│   ├── delivery_service.py
│   └── notification_service.py  # НОВОЕ: Сервис уведомлений
├── external/              # Внешние сервисы
│   ├── qr_service.py
│   ├── telegram_service.py
│   ├── email_service.py
│   └── whatsapp_relay_service.py  # НОВОЕ: WhatsApp Relay
└── utils/                 # Утилиты
    ├── validators.py
    ├── formatters.py
    ├── helpers.py
    └── phone_utils.py     # НОВОЕ: Утилиты для телефонов
```

### **Слой 4: Модели данных (Data Layer)**
```
📁 models/
├── __init__.py
├── base.py                # Базовая модель
├── domain/                # Доменные модели
│   ├── product.py
│   ├── order.py
│   ├── user.py
│   ├── cart.py
│   └── message_log.py     # НОВОЕ: Логи уведомлений
├── repositories/          # Репозитории
│   ├── base_repository.py
│   ├── product_repository.py
│   ├── order_repository.py
│   └── notification_repository.py  # НОВОЕ: Репозиторий уведомлений
└── migrations/            # Миграции БД
    ├── versions/
    └── env.py
```

### **Слой 5: Конфигурация и инфраструктура**
```
📁 config/
├── __init__.py
├── settings.py            # Настройки приложения
├── database.py            # Настройки БД
├── cache.py               # Настройки кеша
├── logging.py             # Настройки логирования
└── notifications.py       # НОВОЕ: Настройки уведомлений

📁 infrastructure/
├── __init__.py
├── database.py            # Подключение к БД
├── cache.py               # Кеш (Redis/Memory)
├── storage.py             # Файловое хранилище
├── monitoring.py          # Мониторинг
└── whatsapp_relay.py      # НОВОЕ: Интеграция с WA Relay
```

### **Слой 6: WhatsApp Relay (Микросервис) - НОВОЕ**
```
📁 wa_relay/
├── package.json
├── server.js              # Основной сервер
├── whatsapp-client.js     # Клиент WhatsApp
├── phone-utils.js         # Утилиты для телефонов
├── message-templates.js   # Шаблоны сообщений
├── validators.js          # Валидация данных
├── rate-limiter.js        # Ограничение скорости
├── .env.example
├── Dockerfile
└── README.md
```

---

## 🔧 ПАТТЕРНЫ И ПРАКТИКИ

### **1. Repository Pattern**
```python
# Базовый репозиторий
class BaseRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, id: int):
        pass
    
    def create(self, obj):
        pass
    
    def update(self, id: int, obj):
        pass
    
    def delete(self, id: int):
        pass

# Репозиторий уведомлений - НОВОЕ
class NotificationRepository(BaseRepository):
    def get_ready_orders(self):
        return self.db.query(Order).filter(
            Order.arrival_status == 'ready'
        ).all()
    
    def get_message_logs_by_batch(self, batch_id: str):
        return self.db.query(MessageLog).filter(
            MessageLog.batch_id == batch_id
        ).all()
    
    def create_message_log(self, log_data: dict):
        log = MessageLog(**log_data)
        self.db.add(log)
        self.db.commit()
        return log
```

### **2. Service Layer Pattern**
```python
class NotificationService:
    def __init__(self, notification_repo: NotificationRepository, 
                 whatsapp_service: WhatsAppRelayService):
        self.notification_repo = notification_repo
        self.whatsapp_service = whatsapp_service
    
    def get_ready_orders(self) -> List[ReadyOrder]:
        # Получение заказов готовых к выдаче
        orders = self.notification_repo.get_ready_orders()
        return [self._convert_to_ready_order(order) for order in orders]
    
    def send_notifications(self, request: NotificationSendRequest) -> NotificationSendResponse:
        # Отправка уведомлений через WhatsApp Relay
        try:
            response = self.whatsapp_service.send_notifications(request)
            self._save_message_logs(response)
            return response
        except Exception as e:
            self._handle_send_error(e)
            raise
    
    def _convert_to_ready_order(self, order: Order) -> ReadyOrder:
        # Конвертация заказа в формат для уведомлений
        pass
    
    def _save_message_logs(self, response: WhatsAppResponse):
        # Сохранение логов отправки
        pass
    
    def _handle_send_error(self, error: Exception):
        # Обработка ошибок отправки
        pass
```

### **3. WhatsApp Relay Service - НОВОЕ**
```python
class WhatsAppRelayService:
    def __init__(self, relay_url: str, auth_token: str):
        self.relay_url = relay_url
        self.auth_token = auth_token
        self.client = httpx.AsyncClient()
    
    async def send_notifications(self, request: NotificationSendRequest) -> WhatsAppResponse:
        """Отправка уведомлений через WhatsApp Relay"""
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                f"{self.relay_url}/wa/notify",
                json=request.dict(),
                headers=headers,
                timeout=300.0  # 5 минут таймаут
            )
            response.raise_for_status()
            return WhatsAppResponse(**response.json())
        except httpx.TimeoutException:
            raise WhatsAppTimeoutError("WhatsApp Relay timeout")
        except httpx.HTTPStatusError as e:
            raise WhatsAppAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise WhatsAppServiceError(f"Unexpected error: {str(e)}")
    
    async def check_health(self) -> bool:
        """Проверка здоровья WhatsApp Relay"""
        try:
            response = await self.client.get(f"{self.relay_url}/wa/health")
            data = response.json()
            return data.get("ok", False) and data.get("clientReady", False)
        except:
            return False
```

### **4. Error Handling Pattern**
```python
# Базовые исключения
class AppException(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)

class ValidationError(AppException):
    pass

class NotFoundError(AppException):
    pass

class BusinessLogicError(AppException):
    pass

# Новые исключения для WhatsApp - НОВОЕ
class WhatsAppServiceError(AppException):
    pass

class WhatsAppAPIError(WhatsAppServiceError):
    pass

class WhatsAppTimeoutError(WhatsAppServiceError):
    pass

class InvalidPhoneError(ValidationError):
    pass

# Обработчик ошибок
@app.exception_handler(WhatsAppServiceError)
async def whatsapp_error_handler(request: Request, exc: WhatsAppServiceError):
    return JSONResponse(
        status_code=503,
        content={"error": "WhatsApp service unavailable", "code": exc.code}
    )

@app.exception_handler(InvalidPhoneError)
async def invalid_phone_error_handler(request: Request, exc: InvalidPhoneError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid phone number", "code": "INVALID_PHONE"}
    )
```

### **5. Configuration Management**
```python
# settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./sirius.db"
    
    # Security
    secret_key: str
    session_max_age: int = 86400
    
    # External services
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # WhatsApp Relay - НОВОЕ
    whatsapp_relay_url: str = "http://localhost:3000"
    whatsapp_relay_token: str
    pickup_address: str = "Наш склад, ул. Примерная, 123"
    pickup_hours: str = "Пн-Пт: 10:00-19:00, Сб: 10:00-16:00"
    default_country_code: str = "BY"
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Глобальный экземпляр
settings = Settings()
```

---

## 🧪 СТРАТЕГИЯ ТЕСТИРОВАНИЯ

### **1. Пирамида тестирования**

#### **Unit Tests (70%)**
```python
# tests/unit/test_notification_service.py - НОВОЕ
import pytest
from unittest.mock import Mock
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationSendRequest

class TestNotificationService:
    def test_get_ready_orders_success(self):
        # Arrange
        mock_repo = Mock()
        mock_whatsapp = Mock()
        service = NotificationService(mock_repo, mock_whatsapp)
        mock_repo.get_ready_orders.return_value = [Mock()]
        
        # Act
        result = service.get_ready_orders()
        
        # Assert
        assert len(result) == 1
        mock_repo.get_ready_orders.assert_called_once()
    
    def test_send_notifications_success(self):
        # Arrange
        mock_repo = Mock()
        mock_whatsapp = Mock()
        service = NotificationService(mock_repo, mock_whatsapp)
        request = NotificationSendRequest(recipients=[])
        mock_whatsapp.send_notifications.return_value = Mock()
        
        # Act
        result = service.send_notifications(request)
        
        # Assert
        mock_whatsapp.send_notifications.assert_called_once_with(request)
        assert result is not None

# tests/unit/test_phone_utils.py - НОВОЕ
import pytest
from app.utils.phone_utils import normalize_phone, validate_phone

class TestPhoneUtils:
    def test_normalize_phone_by_format(self):
        assert normalize_phone("8029XXXXXXX", "BY") == "+37529XXXXXXX"
        assert normalize_phone("29XXXXXXX", "BY") == "+37529XXXXXXX"
        assert normalize_phone("+37529XXXXXXX", "BY") == "+37529XXXXXXX"
    
    def test_validate_phone_valid(self):
        assert validate_phone("+37529XXXXXXX") == True
        assert validate_phone("+375291234567") == True
    
    def test_validate_phone_invalid(self):
        assert validate_phone("123") == False
        assert validate_phone("invalid") == False
```

#### **Integration Tests (20%)**
```python
# tests/integration/test_notification_api.py - НОВОЕ
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_send_notifications_api():
    response = client.post(
        "/api/admin/notifications/send",
        json={
            "template_key": "arrived_v1",
            "recipients": [
                {"phone": "8029XXXXXXX", "name": "Test", "orderId": "A-001"}
            ]
        }
    )
    assert response.status_code in [200, 503]  # 503 если WA Relay недоступен

def test_get_ready_orders_api():
    response = client.get("/api/admin/notifications/ready-orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

#### **E2E Tests (10%)**
```python
# tests/e2e/test_notification_flow.py - НОВОЕ
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_notification_flow():
    driver = webdriver.Chrome()
    try:
        # Логин в админку
        driver.get("http://localhost:8000/admin/login")
        # ... логин ...
        
        # Переход к уведомлениям
        driver.get("http://localhost:8000/admin/notifications")
        
        # Выбор заказов
        checkbox = driver.find_element(By.CSS_SELECTOR, ".order-checkbox")
        checkbox.click()
        
        # Нажатие "Разослать уведомления"
        send_button = driver.find_element(By.CSS_SELECTOR, ".send-notifications-btn")
        send_button.click()
        
        # Проверка модалки
        modal = driver.find_element(By.CSS_SELECTOR, ".notification-modal")
        assert modal.is_displayed()
        
    finally:
        driver.quit()
```

### **2. Автоматизация тестирования**
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      whatsapp-relay:
        image: sirius/wa-relay:latest
        env:
          AUTH_BEARER: test-token
        options: >-
          --health-cmd "curl -f http://localhost:3000/wa/health"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

---

## 📊 МОНИТОРИНГ И ЛОГИРОВАНИЕ

### **1. Структурированное логирование**
```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        # Новые поля для уведомлений - НОВОЕ
        if hasattr(record, 'batch_id'):
            log_entry['batch_id'] = record.batch_id
        if hasattr(record, 'phone_masked'):
            log_entry['phone_masked'] = record.phone_masked
        if hasattr(record, 'whatsapp_status'):
            log_entry['whatsapp_status'] = record.whatsapp_status
            
        return json.dumps(log_entry)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### **2. Health Checks**
```python
# health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.whatsapp_relay_service import WhatsAppRelayService

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    checks = {
        "database": await check_database(db),
        "cache": await check_cache(),
        "storage": await check_storage(),
        "whatsapp_relay": await check_whatsapp_relay(),  # НОВОЕ
        "external_services": await check_external_services()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

async def check_whatsapp_relay() -> bool:  # НОВОЕ
    """Проверка WhatsApp Relay"""
    try:
        whatsapp_service = WhatsAppRelayService(
            settings.whatsapp_relay_url,
            settings.whatsapp_relay_token
        )
        return await whatsapp_service.check_health()
    except Exception:
        return False
```

### **3. Метрики и мониторинг**
```python
# monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Метрики
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users', 'Number of active users')

# Новые метрики для уведомлений - НОВОЕ
WHATSAPP_MESSAGES_SENT = Counter('whatsapp_messages_sent_total', 'Total WhatsApp messages sent', ['status'])
WHATSAPP_MESSAGES_FAILED = Counter('whatsapp_messages_failed_total', 'Total WhatsApp messages failed', ['error_type'])
WHATSAPP_RELAY_STATUS = Gauge('whatsapp_relay_status', 'WhatsApp Relay status (1=up, 0=down)')

# Middleware для сбора метрик
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

---

## 🚀 ДЕПЛОЙ И CI/CD

### **1. Контейнеризация**
```dockerfile
# Dockerfile для основного приложения
FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd --create-home --shell /bin/bash app
USER app

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Dockerfile для WhatsApp Relay - НОВОЕ
FROM node:18-alpine

WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm ci --only=production

# Копирование кода
COPY . .

# Создание пользователя
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
USER nextjs

# Запуск приложения
CMD ["node", "server.js"]
```

### **2. Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/sirius
      - WHATSAPP_RELAY_URL=http://wa-relay:3000
    depends_on:
      - db
      - redis
      - wa-relay
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads

  wa-relay:  # НОВОЕ
    build: ./wa_relay
    ports:
      - "3000:3000"
    environment:
      - AUTH_BEARER=your-secret-token
      - DEFAULT_COUNTRY=BY
    volumes:
      - wa_session:/app/.wwebjs_auth
    depends_on:
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: sirius
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

volumes:
  postgres_data:
  wa_session:  # НОВОЕ
```

### **3. CI/CD Pipeline**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Run tests
      run: pytest tests/
    
    - name: Build Docker images
      run: |
        docker build -t sirius-app .
        docker build -t sirius-wa-relay ./wa_relay
    
    - name: Deploy to production
      run: |
        docker-compose -f docker-compose.prod.yml up -d
        docker system prune -f
```

---

## 🔒 БЕЗОПАСНОСТЬ

### **1. Валидация входных данных**
```python
# validators.py
from pydantic import BaseModel, validator
import re

class NotificationSendRequest(BaseModel):
    template_key: str
    recipients: List[RecipientData]
    dry_run: bool = False
    
    @validator('recipients')
    def validate_recipients(cls, v):
        if not v:
            raise ValueError('At least one recipient required')
        if len(v) > 50:
            raise ValueError('Maximum 50 recipients allowed')
        return v

class RecipientData(BaseModel):
    phone: str
    name: str
    orderId: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        # Нормализация и валидация телефона
        normalized = normalize_phone(v, "BY")
        if not validate_phone(normalized):
            raise ValueError('Invalid phone number format')
        return normalized
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if not re.match(r'^[a-zA-Zа-яА-Я\s\-_]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
```

### **2. Защита от SQL-инъекций**
```python
# Использование параметризованных запросов
def get_product_by_name(db: Session, name: str):
    return db.query(Product).filter(Product.name == name).first()

# НЕ ДЕЛАТЬ ТАК:
# query = f"SELECT * FROM products WHERE name = '{name}'"
```

### **3. Rate Limiting**
```python
# rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/api/admin/notifications/send")
@limiter.limit("5/minute")  # НОВОЕ: Ограничение для уведомлений
async def send_notifications(request: Request, ...):
    # Логика отправки уведомлений
    pass
```

### **4. Безопасность WhatsApp Relay - НОВОЕ**
```javascript
// wa_relay/server.js
const express = require('express');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

const app = express();

// Безопасность
app.use(helmet());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 минут
  max: 100, // максимум 100 запросов
  message: 'Too many requests from this IP'
});
app.use(limiter);

// Аутентификация
app.use((req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (token !== process.env.AUTH_BEARER) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

// Маскирование телефонов в логах
app.use((req, res, next) => {
  const originalSend = res.send;
  res.send = function(data) {
    if (typeof data === 'string') {
      data = data.replace(/(\+375\d{9})/g, '+375****$1.slice(-4)');
    }
    originalSend.call(this, data);
  };
  next();
});
```

---

## 📈 ПРОИЗВОДИТЕЛЬНОСТЬ

### **1. Кеширование**
```python
# cache.py
from functools import wraps
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Попытка получить из кеша
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Выполнение функции
            result = await func(*args, **kwargs)
            
            # Сохранение в кеш
            redis_client.setex(cache_key, expiration, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Использование
@cache_result(expiration=600)
async def get_products(db: Session):
    return db.query(Product).all()

# Кеширование шаблонов уведомлений - НОВОЕ
@cache_result(expiration=3600)
async def get_message_templates():
    return MESSAGE_TEMPLATES
```

### **2. Асинхронность**
```python
# Асинхронные операции
async def process_order_async(order_data: OrderCreate):
    # Параллельное выполнение задач
    tasks = [
        validate_order(order_data),
        check_inventory(order_data.product_id),
        calculate_delivery_cost(order_data.delivery_option),
        generate_qr_code(order_data)
    ]
    
    results = await asyncio.gather(*tasks)
    return results

# Асинхронная отправка уведомлений - НОВОЕ
async def send_notifications_async(recipients: List[RecipientData]):
    # Группировка получателей по батчам
    batches = [recipients[i:i+10] for i in range(0, len(recipients), 10)]
    
    # Параллельная отправка батчей
    tasks = []
    for batch in batches:
        task = asyncio.create_task(send_batch_notifications(batch))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### **3. Пагинация**
```python
# pagination.py
from typing import List, Optional
from sqlalchemy.orm import Query

class Pagination:
    def __init__(self, page: int = 1, size: int = 20, max_size: int = 100):
        self.page = max(1, page)
        self.size = min(max(1, size), max_size)
        self.offset = (self.page - 1) * self.size
    
    def paginate_query(self, query: Query) -> Query:
        return query.offset(self.offset).limit(self.size)
    
    def get_pagination_info(self, total: int) -> dict:
        total_pages = (total + self.size - 1) // self.size
        return {
            "page": self.page,
            "size": self.size,
            "total": total,
            "total_pages": total_pages,
            "has_next": self.page < total_pages,
            "has_prev": self.page > 1
        }

# Пагинация для уведомлений - НОВОЕ
@router.get("/api/admin/notifications/ready-orders")
async def get_ready_orders(
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    pagination = Pagination(page, size)
    query = db.query(Order).filter(Order.arrival_status == 'ready')
    
    total = query.count()
    orders = pagination.paginate_query(query).all()
    
    return {
        "orders": [order.dict() for order in orders],
        "pagination": pagination.get_pagination_info(total)
    }
```

---

## 🎯 РЕКОМЕНДАЦИИ ПО РЕАЛИЗАЦИИ

### **1. Поэтапная разработка**
1. **Неделя 1-2:** Базовая архитектура и модели данных
2. **Неделя 3-4:** API и базовые сервисы
3. **Неделя 5-6:** Веб-интерфейс и шаблоны
4. **Неделя 7-8:** WhatsApp Relay и интеграция - НОВОЕ
5. **Неделя 9-10:** Тестирование и отладка
6. **Неделя 11-12:** Деплой и мониторинг

### **2. Приоритеты функций**
- **Критически важные:** Аутентификация, управление товарами, заказы
- **Важные:** Корзина, QR-коды, базовая аналитика
- **Желательные:** WhatsApp уведомления, расширенная аналитика, интеграции - НОВОЕ

### **3. Контроль качества**
- Code review для каждого PR
- Автоматические тесты при каждом коммите
- Регулярные рефакторинги
- Документация обновляется вместе с кодом

### **4. Мониторинг в продакшене**
- Логирование всех операций
- Алерты на критические ошибки
- Регулярные бэкапы БД
- Мониторинг производительности
- **Мониторинг WhatsApp Relay** - НОВОЕ

---

## 📋 ЧЕКЛИСТ ГОТОВНОСТИ

### **Перед запуском в продакшн:**
- [ ] Все тесты проходят
- [ ] Код покрыт тестами минимум на 80%
- [ ] Документация актуальна
- [ ] Настроен мониторинг
- [ ] Проведено нагрузочное тестирование
- [ ] Настроены бэкапы
- [ ] Проверена безопасность
- [ ] Настроен CI/CD
- [ ] Подготовлен план отката
- [ ] **WhatsApp Relay протестирован** - НОВОЕ
- [ ] **Уведомления работают корректно** - НОВОЕ

### **После запуска:**
- [ ] Мониторинг работает
- [ ] Логи пишутся корректно
- [ ] Производительность в норме
- [ ] Пользователи могут работать
- [ ] Критические функции работают
- [ ] План поддержки готов
- [ ] **WhatsApp уведомления доставляются** - НОВОЕ

---

**Этот план поможет создать надежную, масштабируемую и поддерживаемую систему с WhatsApp уведомлениями, которая будет работать стабильно и не будет падать при изменениях.**
