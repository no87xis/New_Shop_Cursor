#!/bin/bash

echo "🔧 Настройка Sirius Shop..."

# Обновить систему
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установить необходимые пакеты
echo "📦 Установка зависимостей..."
apt install -y python3 python3-pip python3-venv git curl

# Создать папку проекта
echo "📁 Создание папки проекта..."
mkdir -p ~/sirius_shop
cd ~/sirius_shop

# Создать виртуальное окружение
echo "🐍 Создание виртуального окружения..."
python3 -m venv venv

# Активировать виртуальное окружение
echo "📦 Активация виртуального окружения..."
source venv/bin/activate

# Установить зависимости
echo "📦 Установка Python зависимостей..."
pip install -r requirements.txt

# Создать необходимые папки
echo "📁 Создание папок..."
mkdir -p logs uploads/products

# Сделать скрипт запуска исполняемым
chmod +x start_server.sh

echo "✅ Настройка завершена!"
echo ""
echo "🚀 Для запуска сервера выполните:"
echo "   cd ~/sirius_shop"
echo "   ./start_server.sh"
echo ""
echo "📍 После запуска сервер будет доступен по адресу:"
echo "   http://185.239.50.157:8000"