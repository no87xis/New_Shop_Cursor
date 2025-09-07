#!/bin/bash

echo "🚀 Запуск Sirius Shop..."

# Перейти в папку проекта
cd ~/sirius_shop

# Активировать виртуальное окружение
echo "📦 Активация виртуального окружения..."
source venv/bin/activate

# Создать папки если не существуют
echo "📁 Создание необходимых папок..."
mkdir -p logs uploads/products

# Создать базу данных и таблицы
echo "🗄️ Создание базы данных..."
python -c "
from app.db import engine, Base
from app.models import product, shop_cart, shop_order
Base.metadata.create_all(bind=engine)
print('✅ База данных создана!')
"

# Создать тестовые данные
echo "📊 Создание тестовых данных..."
python -c "
from app.db import SessionLocal
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate
from datetime import date, timedelta

db = SessionLocal()
product_service = ProductService(db)

# Проверяем, есть ли уже товары
existing_products = product_service.get_all()
if len(existing_products) == 0:
    # Создаем тестовые товары
    test_products = [
        ProductCreate(
            name='iPhone 15 Pro',
            description='Новейший смартфон от Apple с титановым корпусом',
            quantity=5,
            min_stock=2,
            buy_price_eur=800.0,
            sell_price_rub=120000.0,
            supplier_name='Apple Inc.',
            availability_status='IN_STOCK'
        ),
        ProductCreate(
            name='Samsung Galaxy S24',
            description='Флагманский Android смартфон с AI функциями',
            quantity=0,
            min_stock=3,
            buy_price_eur=700.0,
            sell_price_rub=95000.0,
            supplier_name='Samsung Electronics',
            availability_status='ON_ORDER'
        ),
        ProductCreate(
            name='MacBook Pro M3',
            description='Профессиональный ноутбук с чипом M3',
            quantity=2,
            min_stock=1,
            buy_price_eur=1500.0,
            sell_price_rub=200000.0,
            supplier_name='Apple Inc.',
            availability_status='IN_TRANSIT',
            expected_date=date.today() + timedelta(days=7)
        ),
        ProductCreate(
            name='AirPods Pro 2',
            description='Беспроводные наушники с активным шумоподавлением',
            quantity=10,
            min_stock=5,
            buy_price_eur=200.0,
            sell_price_rub=25000.0,
            supplier_name='Apple Inc.',
            availability_status='IN_STOCK'
        )
    ]
    
    for product_data in test_products:
        product_service.create(product_data)
    
    print('✅ Тестовые данные созданы!')
else:
    print('ℹ️ Тестовые данные уже существуют')

db.close()
"

# Запустить сервер
echo "🌐 Запуск сервера на порту 8000..."
echo "📍 Доступные адреса:"
echo "   - Локальный: http://localhost:8000"
echo "   - Внешний: http://185.239.50.157:8000"
echo "   - Админ панель: http://185.239.50.157:8000/admin"
echo ""
echo "⏹️ Для остановки нажмите Ctrl+C"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload