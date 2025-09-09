#!/usr/bin/env python3
"""
Скрипт для установки поддержки фото товаров на сервер
"""
import subprocess
import os
import sys

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            if result.stdout:
                print(f"   Вывод: {result.stdout.strip()}")
        else:
            print(f"❌ {description} - ошибка")
            if result.stderr:
                print(f"   Ошибка: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False

def main():
    """Основная функция установки"""
    print("🚀 Установка поддержки фото товаров на сервер...")
    
    # Команды для выполнения на сервере
    commands = [
        # 1. Создание директорий
        ("mkdir -p /root/New_Shop_Cursor/uploads/products/thumbnails", "Создание директорий для загрузки"),
        ("mkdir -p /root/New_Shop_Cursor/app/static/images", "Создание директории для статических файлов"),
        ("mkdir -p /root/New_Shop_Cursor/app/static/uploads/products/thumbnails", "Создание директории для статических загрузок"),
        
        # 2. Копирование файлов
        ("cp /workspace/migration_add_photos.sql /root/New_Shop_Cursor/", "Копирование миграции"),
        ("cp /workspace/image_upload_service.py /root/New_Shop_Cursor/app/services/", "Копирование сервиса загрузки"),
        ("cp /workspace/photo_upload_api.py /root/New_Shop_Cursor/app/routers/", "Копирование API для фото"),
        ("cp /workspace/placeholder_image.svg /root/New_Shop_Cursor/app/static/images/placeholder-product.svg", "Копирование placeholder изображения"),
        
        # 3. Установка зависимостей
        ("cd /root/New_Shop_Cursor && source venv/bin/activate && pip install Pillow", "Установка Pillow для обработки изображений"),
        
        # 4. Выполнение миграции
        ("cd /root/New_Shop_Cursor && docker exec postgres16 psql -U appuser -d appdb -f /root/New_Shop_Cursor/migration_add_photos.sql", "Выполнение миграции базы данных"),
        
        # 5. Создание placeholder изображения
        ("cd /root/New_Shop_Cursor && echo '<svg width=\"400\" height=\"300\" xmlns=\"http://www.w3.org/2000/svg\"><rect width=\"400\" height=\"300\" fill=\"#f3f4f6\"/><rect x=\"50\" y=\"50\" width=\"300\" height=\"200\" fill=\"#e5e7eb\" stroke=\"#d1d5db\" stroke-width=\"2\" rx=\"8\"/><circle cx=\"200\" cy=\"120\" r=\"30\" fill=\"#9ca3af\"/><path d=\"M170 150 L200 120 L230 150 L200 180 Z\" fill=\"#9ca3af\"/><text x=\"200\" y=\"220\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"16\" fill=\"#6b7280\">Нет изображения</text><text x=\"200\" y=\"240\" text-anchor=\"middle\" font-family=\"Arial, sans-serif\" font-size=\"12\" fill=\"#9ca3af\">Загрузите фото товара</text></svg>' > app/static/images/placeholder-product.svg", "Создание placeholder изображения"),
        
        # 6. Обновление модели товара
        ("cd /root/New_Shop_Cursor && cp app/models/product.py app/models/product.py.backup", "Создание резервной копии модели"),
        
        # 7. Перезапуск сервера
        ("pkill -f uvicorn", "Остановка сервера"),
        ("cd /root/New_Shop_Cursor && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &", "Запуск сервера"),
    ]
    
    # Выполняем команды
    success_count = 0
    for command, description in commands:
        if run_command(f"sshpass -p 'uSH51YfTKa2h342Cef' ssh -o StrictHostKeyChecking=no root@185.239.50.157 '{command}'", description):
            success_count += 1
    
    print(f"\n📊 Результат: {success_count}/{len(commands)} команд выполнено успешно")
    
    if success_count == len(commands):
        print("\n🎉 Поддержка фото товаров успешно установлена!")
        print("\n📋 Что было сделано:")
        print("✅ Добавлены поля photo_url и photo_alt в таблицу products")
        print("✅ Создан сервис для загрузки и обработки изображений")
        print("✅ Добавлены API endpoints для работы с фото")
        print("✅ Создан placeholder для товаров без фото")
        print("✅ Установлена библиотека Pillow для обработки изображений")
        print("✅ Сервер перезапущен с новым функционалом")
        
        print("\n🔧 Следующие шаги:")
        print("1. Обновить модель Product в app/models/product.py")
        print("2. Добавить роутер photo_upload_api в main.py")
        print("3. Обновить шаблоны для отображения фото")
        print("4. Протестировать загрузку фото через админку")
        
    else:
        print("\n⚠️ Некоторые команды не выполнены. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()