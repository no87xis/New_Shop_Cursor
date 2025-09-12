#!/usr/bin/env python3
"""
Скрипт для очистки базы данных и создания новых товаров
"""
from app.db import get_db
from app.models import *
from sqlalchemy import text

def reset_database():
    # Подключаемся к базе
    db = next(get_db())
    
    try:
        # Очищаем все таблицы в правильном порядке (сначала зависимые)
        print('Очищаю базу данных...')
        
        # 1. Сначала удаляем корзины (зависят от товаров)
        db.execute(text('DELETE FROM shop_carts'))
        print('Корзины очищены')
        
        # 2. Удаляем заказы
        db.execute(text('DELETE FROM shop_orders'))
        print('Заказы очищены')
        
        # 3. Удаляем товары
        db.execute(text('DELETE FROM products'))
        print('Товары очищены')
        
        # 4. Удаляем способы оплаты
        db.execute(text('DELETE FROM payment_methods'))
        print('Способы оплаты очищены')
        
        db.commit()
        print('База данных полностью очищена!')
        
        # Создаем новые товары
        print('Создаю новые товары...')
        
        # Товар 1
        db.execute(text("""
        INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
        VALUES ('iPhone 15 Pro', 'Новейший iPhone с титановым корпусом', 99990, '/static/images/iphone15.jpg', 'IN_STOCK', NOW(), NOW())
        """))
        
        # Товар 2  
        db.execute(text("""
        INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
        VALUES ('MacBook Air M2', 'Ультратонкий ноутбук с чипом M2', 129990, '/static/images/macbook.jpg', 'IN_STOCK', NOW(), NOW())
        """))
        
        # Товар 3
        db.execute(text("""
        INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
        VALUES ('AirPods Pro 2', 'Беспроводные наушники с шумоподавлением', 24990, '/static/images/airpods.jpg', 'IN_STOCK', NOW(), NOW())
        """))
        
        # Товар 4
        db.execute(text("""
        INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
        VALUES ('Apple Watch Series 9', 'Умные часы с датчиком здоровья', 39990, '/static/images/watch.jpg', 'IN_STOCK', NOW(), NOW())
        """))
        
        # Товар 5
        db.execute(text("""
        INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
        VALUES ('iPad Pro 12.9', 'Планшет для профессионалов', 89990, '/static/images/ipad.jpg', 'IN_STOCK', NOW(), NOW())
        """))
        
        db.commit()
        print('Новые товары созданы!')
        
        # Проверяем товары
        result = db.execute(text('SELECT id, name, price_rub FROM products ORDER BY id'))
        products = result.fetchall()
        print('Созданные товары:')
        for product in products:
            print(f'ID: {product[0]}, Название: {product[1]}, Цена: {product[2]}₽')
            
        print('Готово!')
        
    except Exception as e:
        print(f'Ошибка: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()