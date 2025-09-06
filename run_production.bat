@echo off
echo ========================================
echo    Sirius Group V2 - Продакшен запуск
echo ========================================

REM Проверка Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Docker не найден!
    echo Установите Docker Desktop и попробуйте снова.
    pause
    exit /b 1
)

REM Проверка Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Docker Compose не найден!
    echo Установите Docker Compose и попробуйте снова.
    pause
    exit /b 1
)

echo Docker и Docker Compose найдены.

REM Создание необходимых папок
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "backups" mkdir backups
if not exist "ssl" mkdir ssl

echo Создание необходимых папок...

REM Проверка SSL сертификатов
if not exist "ssl\cert.pem" (
    echo ВНИМАНИЕ: SSL сертификаты не найдены!
    echo Создайте самоподписанные сертификаты или добавьте реальные.
    echo.
    echo Для создания самоподписанных сертификатов:
    echo openssl req -x509 -newkey rsa:4096 -keyout ssl\key.pem -out ssl\cert.pem -days 365 -nodes
    echo.
    pause
)

REM Сборка и запуск контейнеров
echo Сборка Docker образов...
docker-compose build

if errorlevel 1 (
    echo ОШИБКА: Ошибка сборки Docker образов!
    pause
    exit /b 1
)

echo Запуск контейнеров...
docker-compose up -d

if errorlevel 1 (
    echo ОШИБКА: Ошибка запуска контейнеров!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Система запущена успешно!
echo ========================================
echo.
echo Сервисы доступны по адресам:
echo - Основное приложение: https://localhost
echo - API документация: https://localhost/docs
echo - Админ панель: https://localhost/admin
echo - Магазин: https://localhost/shop/
echo.
echo Для остановки системы выполните:
echo docker-compose down
echo.
echo Для просмотра логов:
echo docker-compose logs -f
echo.

pause