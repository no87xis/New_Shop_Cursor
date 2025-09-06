@echo off
echo ========================================
echo    Sirius Group V2 - Тестирование системы
echo ========================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    pause
    exit /b 1
)

echo 1. Проверка синтаксиса...
python -c "import ast; ast.parse(open('app/main.py').read()); print('Syntax OK')"
if %errorlevel% neq 0 (
    echo ОШИБКА: Синтаксическая ошибка
    exit /b 1
)

echo 2. Проверка импортов...
python -c "from app.main import app; print('Imports OK')"
if %errorlevel% neq 0 (
    echo ОШИБКА: Ошибка импорта
    exit /b 1
)

echo 3. Проверка конфигурации...
python -c "from app.config import settings; print('Config OK:', settings.environment)"
if %errorlevel% neq 0 (
    echo ОШИБКА: Ошибка конфигурации
    exit /b 1
)

echo 4. Проверка базы данных...
python -c "from app.db import check_database_connection; print('DB OK:', check_database_connection())"
if %errorlevel% neq 0 (
    echo ОШИБКА: Ошибка базы данных
    exit /b 1
)

echo 5. Запуск базовых тестов...
python -m pytest tests/test_basic.py -v
if %errorlevel% neq 0 (
    echo ОШИБКА: Тесты не прошли
    exit /b 1
)

echo.
echo Все проверки пройдены успешно!
echo Система готова к работе.
echo.

pause