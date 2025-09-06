@echo off
echo ========================================
echo    Sirius Group V2 - Резервное копирование
echo ========================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    pause
    exit /b 1
)

REM Создание резервной копии
echo Создание резервной копии...
python -c "
from app.backup import backup_manager
import os

# Создание резервной копии
source_paths = ['app', 'templates', 'static']
if os.path.exists('wa_relay'):
    source_paths.append('wa_relay')

backup_path = backup_manager.create_backup(source_paths)
print(f'Резервная копия создана: {backup_path}')

# Показываем список всех бэкапов
backups = backup_manager.list_backups()
print(f'Всего резервных копий: {len(backups)}')
for backup in backups[:5]:  # Показываем последние 5
    print(f'  - {backup[\"name\"]} ({backup[\"size\"]} bytes)')
"

if errorlevel 1 (
    echo ОШИБКА: Не удалось создать резервную копию!
    pause
    exit /b 1
)

echo.
echo Резервная копия создана успешно!
echo Файл находится в папке backups/
echo.

pause