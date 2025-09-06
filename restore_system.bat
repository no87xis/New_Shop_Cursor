@echo off
echo ========================================
echo    Sirius Group V2 - Восстановление системы
echo ========================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    pause
    exit /b 1
)

REM Показываем доступные резервные копии
echo Доступные резервные копии:
python -c "
from app.backup import backup_manager
import os

backups = backup_manager.list_backups()
if not backups:
    print('Резервные копии не найдены!')
    exit(1)

print('Доступные резервные копии:')
for i, backup in enumerate(backups, 1):
    print(f'{i}. {backup[\"name\"]} - {backup[\"created\"]} ({backup[\"size\"]} bytes)')
"

if errorlevel 1 (
    echo ОШИБКА: Не удалось получить список резервных копий!
    pause
    exit /b 1
)

echo.
set /p choice="Выберите номер резервной копии для восстановления (или 0 для отмены): "

if "%choice%"=="0" (
    echo Восстановление отменено.
    pause
    exit /b 0
)

REM Восстановление
echo Восстановление из резервной копии...
python -c "
from app.backup import backup_manager
import sys

backups = backup_manager.list_backups()
try:
    choice = int('%choice%') - 1
    if 0 <= choice < len(backups):
        backup = backups[choice]
        print(f'Восстановление из: {backup[\"name\"]}')
        success = backup_manager.restore_backup(backup['path'])
        if success:
            print('Восстановление завершено успешно!')
        else:
            print('Ошибка восстановления!')
            sys.exit(1)
    else:
        print('Неверный номер резервной копии!')
        sys.exit(1)
except ValueError:
    print('Неверный ввод!')
    sys.exit(1)
"

if errorlevel 1 (
    echo ОШИБКА: Не удалось восстановить резервную копию!
    pause
    exit /b 1
)

echo.
echo Восстановление завершено успешно!
echo.

pause