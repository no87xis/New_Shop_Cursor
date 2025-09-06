@echo off
echo ========================================
echo    Sirius Group V2 - Запуск сервера
echo ========================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    pause
    exit /b 1
)

REM Создание необходимых папок
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "backups" mkdir backups

echo Создание необходимых папок...

REM Проверка синтаксиса
echo Проверка синтаксиса...
python -c "import ast; ast.parse(open('app/main.py').read()); print('Syntax OK')"
if %errorlevel% neq 0 (
    echo ОШИБКА: Синтаксическая ошибка в app/main.py
    pause
    exit /b 1
)

REM Проверка импортов
echo Проверка импортов...
python -c "from app.main import app; print('Imports OK')"
if %errorlevel% neq 0 (
    echo ОШИБКА: Ошибка импорта модулей
    pause
    exit /b 1
)

REM Запуск сервера
echo Запуск сервера...
echo Сервер будет доступен по адресу: http://127.0.0.1:8000
echo Для остановки нажмите Ctrl+C
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause