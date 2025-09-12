-- Отключаем проверку внешних ключей
SET session_replication_role = replica;

-- Очищаем все таблицы
DELETE FROM shop_carts;
DELETE FROM shop_orders;
DELETE FROM products;
DELETE FROM payment_methods;

-- Включаем обратно проверку внешних ключей
SET session_replication_role = DEFAULT;

-- Создаем новые товары
INSERT INTO products (name, description, price_rub, photo_url, availability_status, created_at, updated_at)
VALUES 
('iPhone 15 Pro', 'Новейший iPhone с титановым корпусом', 99990, '/static/images/iphone15.jpg', 'IN_STOCK', NOW(), NOW()),
('MacBook Air M2', 'Ультратонкий ноутбук с чипом M2', 129990, '/static/images/macbook.jpg', 'IN_STOCK', NOW(), NOW()),
('AirPods Pro 2', 'Беспроводные наушники с шумоподавлением', 24990, '/static/images/airpods.jpg', 'IN_STOCK', NOW(), NOW()),
('Apple Watch Series 9', 'Умные часы с датчиком здоровья', 39990, '/static/images/watch.jpg', 'IN_STOCK', NOW(), NOW()),
('iPad Pro 12.9', 'Планшет для профессионалов', 89990, '/static/images/ipad.jpg', 'IN_STOCK', NOW(), NOW());

-- Проверяем результат
SELECT id, name, price_rub FROM products ORDER BY id;