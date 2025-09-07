#!/bin/bash

# Sirius Group V2 - Скрипт автоматического развертывания
# Использование: ./deploy.sh [docker|manual]

set -e

echo "🚀 Sirius Group V2 - Автоматическое развертывание"
echo "=================================================="

# Проверка аргументов
DEPLOYMENT_TYPE=${1:-docker}

if [ "$DEPLOYMENT_TYPE" = "docker" ]; then
    echo "📦 Развертывание через Docker..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker не установлен. Устанавливаем..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose не установлен. Устанавливаем..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Клонирование репозитория
    if [ ! -d "New_Shop_Cursor" ]; then
        echo "📥 Клонирование репозитория..."
        git clone https://github.com/no87xis/New_Shop_Cursor.git
    fi
    
    cd New_Shop_Cursor
    
    # Настройка конфигурации
    if [ ! -f ".env" ]; then
        echo "⚙️ Создание конфигурации..."
        cp .env.production .env
        echo "⚠️  ВАЖНО: Отредактируйте файл .env с вашими настройками!"
        echo "   nano .env"
        read -p "Нажмите Enter после настройки .env файла..."
    fi
    
    # Создание необходимых папок
    mkdir -p logs uploads backups ssl
    
    # Запуск сервисов
    echo "🚀 Запуск сервисов..."
    docker-compose up -d
    
    echo "✅ Развертывание завершено!"
    echo "🌐 Приложение доступно по адресу: http://your-server-ip:8000"
    echo "📊 Админ панель: http://your-server-ip:8000/admin"
    echo "📚 API документация: http://your-server-ip:8000/docs"
    
elif [ "$DEPLOYMENT_TYPE" = "manual" ]; then
    echo "🐍 Ручное развертывание через Python..."
    
    # Обновление системы
    sudo apt update && sudo apt upgrade -y
    
    # Установка Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        echo "📦 Установка Python 3.11..."
        sudo apt install python3.11 python3.11-venv python3.11-dev -y
    fi
    
    # Установка PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo "🐘 Установка PostgreSQL..."
        sudo apt install postgresql postgresql-contrib -y
    fi
    
    # Установка Redis
    if ! command -v redis-server &> /dev/null; then
        echo "🔴 Установка Redis..."
        sudo apt install redis-server -y
    fi
    
    # Установка Nginx
    if ! command -v nginx &> /dev/null; then
        echo "🌐 Установка Nginx..."
        sudo apt install nginx -y
    fi
    
    # Клонирование репозитория
    if [ ! -d "New_Shop_Cursor" ]; then
        echo "📥 Клонирование репозитория..."
        git clone https://github.com/no87xis/New_Shop_Cursor.git
    fi
    
    cd New_Shop_Cursor
    
    # Создание виртуального окружения
    echo "🐍 Создание виртуального окружения..."
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Установка зависимостей
    echo "📦 Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Настройка базы данных
    echo "🗄️ Настройка базы данных..."
    sudo -u postgres psql -c "CREATE DATABASE sirius_db;"
    sudo -u postgres psql -c "CREATE USER sirius WITH PASSWORD 'sirius_password';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sirius_db TO sirius;"
    
    # Настройка конфигурации
    if [ ! -f ".env" ]; then
        echo "⚙️ Создание конфигурации..."
        cp .env.production .env
        echo "⚠️  ВАЖНО: Отредактируйте файл .env с вашими настройками!"
        echo "   nano .env"
        read -p "Нажмите Enter после настройки .env файла..."
    fi
    
    # Создание необходимых папок
    mkdir -p logs uploads backups
    
    # Инициализация базы данных
    echo "🗄️ Инициализация базы данных..."
    python -c "from app.db import create_tables; create_tables()"
    
    # Создание systemd сервиса
    echo "🔧 Создание systemd сервиса..."
    sudo tee /etc/systemd/system/sirius-group.service > /dev/null <<EOF
[Unit]
Description=Sirius Group V2
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    # Запуск сервисов
    sudo systemctl daemon-reload
    sudo systemctl enable sirius-group
    sudo systemctl start sirius-group
    
    echo "✅ Развертывание завершено!"
    echo "🌐 Приложение доступно по адресу: http://your-server-ip:8000"
    echo "📊 Админ панель: http://your-server-ip:8000/admin"
    echo "📚 API документация: http://your-server-ip:8000/docs"
    echo "🔧 Управление сервисом: sudo systemctl status sirius-group"
    
else
    echo "❌ Неверный тип развертывания. Используйте: docker или manual"
    exit 1
fi

echo ""
echo "🎉 Развертывание завершено успешно!"
echo "📋 Следующие шаги:"
echo "   1. Настройте .env файл с вашими параметрами"
echo "   2. Настройте WhatsApp Relay сервис"
echo "   3. Настройте SSL сертификаты для HTTPS"
echo "   4. Настройте мониторинг и логирование"