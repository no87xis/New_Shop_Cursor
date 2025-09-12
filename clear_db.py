#!/usr/bin/env python3
import psycopg2

# Подключаемся к базе
conn = psycopg2.connect(
    host='localhost',
    database='new_shop_cursor',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

try:
    # Отключаем проверку внешних ключей
    cur.execute('SET session_replication_role = replica')
    
    # Очищаем все таблицы
    print('Очищаю все таблицы...')
    cur.execute('DELETE FROM shop_carts')
    cur.execute('DELETE FROM shop_orders')
    cur.execute('DELETE FROM products')
    cur.execute('DELETE FROM payment_methods')
    
    # Включаем обратно проверку внешних ключей
    cur.execute('SET session_replication_role = DEFAULT')
    
    # Создаем новые товары
    print('Создаю новые товары...')
    products = [
        ('iPhone 15 Pro', 'Новейший iPhone с титановым корпусом', 99990),
        ('MacBook Air M2', 'Ультратонкий ноутбук с чипом M2', 129990),
        ('AirPods Pro 2', 'Беспроводные наушники с шумоподавлением', 24990),
        ('Apple Watch Series 9', 'Умные часы с датчиком здоровья', 39990),
        ('iPad Pro 12.9', 'Планшет для профессионалов', 89990)
    ]
    
    for name, desc, price in products:
        cur.execute("""
        INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
        VALUES (%s, %s, %s, '/static/images/product.jpg', 'IN_STOCK', NOW(), NOW())
        """, (name, desc, price))
    
    conn.commit()
    print('Новые товары созданы!')
    
    # Проверяем товары
    cur.execute('SELECT id, name, price_rub FROM products ORDER BY id')
    products = cur.fetchall()
    print('Созданные товары:')
    for product in products:
        print(f'ID: {product[0]}, Название: {product[1]}, Цена: {product[2]}₽')
        
    print('Готово!')
    
except Exception as e:
    print(f'Ошибка: {e}')
    conn.rollback()
finally:
    cur.close()
    conn.close()