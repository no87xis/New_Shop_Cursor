-- Миграция для добавления поля photo_url в таблицу products
ALTER TABLE products ADD COLUMN IF NOT EXISTS photo_url VARCHAR(500);
ALTER TABLE products ADD COLUMN IF NOT EXISTS photo_alt VARCHAR(200);
ALTER TABLE products ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Создание индекса для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_products_photo_url ON products(photo_url);

-- Обновление существующих товаров с placeholder изображениями
UPDATE products SET 
    photo_url = '/static/images/placeholder-product.jpg',
    photo_alt = 'Изображение товара'
WHERE photo_url IS NULL;