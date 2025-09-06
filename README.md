# Sirius Group V2

Система управления складом и интернет-магазин с WhatsApp уведомлениями клиентам.

## 🚀 Возможности

- **Интернет-магазин** с корзиной и системой заказов
- **Управление складом** с отслеживанием остатков
- **QR-коды** для отслеживания заказов
- **Система доставки** с 5 вариантами
- **WhatsApp уведомления** клиентам при поступлении товара
- **Аналитика и отчеты**
- **Ролевая система доступа**

## 📋 Требования

- Python 3.8+
- SQLite (или PostgreSQL для продакшена)
- WhatsApp Relay сервис

## 🛠️ Установка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd sirius-group-v2
```

2. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

3. **Настройка окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

4. **Инициализация базы данных**
```bash
python -c "from app.db import create_tables; create_tables()"
```

5. **Запуск сервера**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 Конфигурация

Основные настройки в файле `.env`:

```env
# База данных
DATABASE_URL=sqlite:///./sirius.db

# Безопасность
SECRET_KEY=your-secret-key-32-characters-long-2024

# WhatsApp Relay
WHATSAPP_RELAY_URL=http://localhost:3000
WHATSAPP_RELAY_TOKEN=your-wa-relay-token

# Адрес пункта выдачи
PICKUP_ADDRESS=Наш склад, ул. Примерная, 123
PICKUP_HOURS=Пн-Пт: 10:00-19:00, Сб: 10:00-16:00
```

## 📱 WhatsApp уведомления

Система поддерживает автоматические уведомления клиентам:

- **Уведомление о прибытии товара** - когда заказ готов к выдаче
- **Уведомление о готовности** - когда товар поступил на склад
- **Уведомление об отправке** - когда заказ отправлен

### Настройка WhatsApp Relay

1. Установите WhatsApp Relay сервис
2. Настройте подключение в `.env`
3. Проверьте статус: `GET /api/notifications/health`

## 🏪 Использование

### Магазин
- Главная страница: `http://localhost:8000/`
- Каталог товаров: `http://localhost:8000/shop/`
- Корзина: `http://localhost:8000/shop/cart`

### Администрирование
- Панель администратора: `http://localhost:8000/admin`
- Управление товарами: `http://localhost:8000/admin/products`
- Управление заказами: `http://localhost:8000/admin/orders`
- Уведомления: `http://localhost:8000/admin/notifications`

### API
- Документация: `http://localhost:8000/docs`
- API товаров: `http://localhost:8000/api/admin/products`
- API заказов: `http://localhost:8000/api/admin/shop-orders`
- API уведомлений: `http://localhost:8000/api/notifications`

## 🔍 Отслеживание заказов

Клиенты могут отслеживать свои заказы:

- По номеру заказа: `http://localhost:8000/track/{order_code}`
- С QR-кодом: `http://localhost:8000/track/{order_code}/qr`

## 🧪 Тестирование

```bash
# Запуск тестов
pytest tests/

# Проверка системы
python test_system.bat
```

## 📊 Мониторинг

- Проверка здоровья: `GET /health`
- Детальная проверка: `GET /health/detailed`
- Метрики: `GET /api/admin/statistics/overview`

## 🔒 Безопасность

- Все API требуют авторизации (кроме публичных)
- Валидация входных данных
- Защита от SQL-инъекций
- Ограничение скорости запросов

## 🚀 Развертывание

### Docker (рекомендуется)

```bash
# Сборка образа
docker build -t sirius-group-v2 .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env sirius-group-v2
```

### Продакшен

1. Используйте PostgreSQL вместо SQLite
2. Настройте Nginx как reverse proxy
3. Используйте SSL сертификаты
4. Настройте мониторинг и логирование

## 📝 API Документация

Полная документация API доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Поддержка

При возникновении проблем:

1. Проверьте логи в папке `logs/`
2. Убедитесь в правильности конфигурации
3. Проверьте статус всех сервисов
4. Обратитесь к документации API

## 📄 Лицензия

Проект разработан для Sirius Group. Все права защищены.

---

**Sirius Group V2** - Современная система управления складом и интернет-магазин с WhatsApp уведомлениями.