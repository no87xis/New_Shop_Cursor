"""
Система резервного копирования Sirius Group V2
"""
import os
import shutil
import zipfile
import json
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Менеджер резервного копирования"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Создание папки для резервных копий"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"Created backup directory: {self.backup_dir}")
    
    def create_backup(self, source_paths: List[str], name: str = None) -> str:
        """
        Создание резервной копии
        
        Args:
            source_paths: Список путей для резервного копирования
            name: Имя резервной копии (если не указано, генерируется автоматически)
            
        Returns:
            Путь к созданной резервной копии
        """
        try:
            # Генерируем имя файла
            if not name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name = f"sirius_backup_{timestamp}"
            
            backup_path = os.path.join(self.backup_dir, f"{name}.zip")
            
            # Создаем ZIP архив
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for source_path in source_paths:
                    if os.path.exists(source_path):
                        if os.path.isfile(source_path):
                            # Файл
                            zipf.write(source_path, os.path.basename(source_path))
                        else:
                            # Папка
                            for root, dirs, files in os.walk(source_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, os.path.dirname(source_path))
                                    zipf.write(file_path, arcname)
            
            # Создаем метаданные
            metadata = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "source_paths": source_paths,
                "size": os.path.getsize(backup_path),
                "files_count": self._count_files_in_zip(backup_path)
            }
            
            metadata_path = os.path.join(self.backup_dir, f"{name}_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str, target_dir: str = ".") -> bool:
        """
        Восстановление из резервной копии
        
        Args:
            backup_path: Путь к резервной копии
            target_dir: Целевая директория для восстановления
            
        Returns:
            True если восстановление успешно
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Создаем резервную копию текущего состояния
            current_backup = self.create_backup(
                ["app", "templates", "static"],
                f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            logger.info(f"Created pre-restore backup: {current_backup}")
            
            # Восстанавливаем файлы
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(target_dir)
            
            logger.info(f"Backup restored successfully from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        Получение списка резервных копий
        
        Returns:
            Список резервных копий с метаданными
        """
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    name = filename[:-4]  # Убираем .zip
                    backup_path = os.path.join(self.backup_dir, filename)
                    metadata_path = os.path.join(self.backup_dir, f"{name}_metadata.json")
                    
                    # Получаем метаданные
                    metadata = {}
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except Exception as e:
                            logger.warning(f"Error reading metadata for {name}: {e}")
                    
                    # Информация о файле
                    stat = os.stat(backup_path)
                    backup_info = {
                        "name": name,
                        "path": backup_path,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        **metadata
                    }
                    
                    backups.append(backup_info)
            
            # Сортируем по дате создания (новые сначала)
            backups.sort(key=lambda x: x.get('created', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def delete_backup(self, name: str) -> bool:
        """
        Удаление резервной копии
        
        Args:
            name: Имя резервной копии
            
        Returns:
            True если удаление успешно
        """
        try:
            backup_path = os.path.join(self.backup_dir, f"{name}.zip")
            metadata_path = os.path.join(self.backup_dir, f"{name}_metadata.json")
            
            if os.path.exists(backup_path):
                os.remove(backup_path)
                logger.info(f"Deleted backup file: {backup_path}")
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                logger.info(f"Deleted metadata file: {metadata_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup {name}: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """
        Очистка старых резервных копий
        
        Args:
            keep_count: Количество резервных копий для сохранения
            
        Returns:
            Количество удаленных резервных копий
        """
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return 0
            
            deleted_count = 0
            for backup in backups[keep_count:]:
                if self.delete_backup(backup['name']):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
            return 0
    
    def _count_files_in_zip(self, zip_path: str) -> int:
        """Подсчет файлов в ZIP архиве"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                return len(zipf.namelist())
        except Exception:
            return 0
    
    def get_backup_info(self, name: str) -> Dict[str, Any]:
        """
        Получение информации о резервной копии
        
        Args:
            name: Имя резервной копии
            
        Returns:
            Информация о резервной копии
        """
        try:
            backup_path = os.path.join(self.backup_dir, f"{name}.zip")
            metadata_path = os.path.join(self.backup_dir, f"{name}_metadata.json")
            
            if not os.path.exists(backup_path):
                return {}
            
            # Базовая информация
            stat = os.stat(backup_path)
            info = {
                "name": name,
                "path": backup_path,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "exists": True
            }
            
            # Метаданные
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        info.update(metadata)
                except Exception as e:
                    logger.warning(f"Error reading metadata for {name}: {e}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting backup info for {name}: {e}")
            return {}


# Глобальный экземпляр менеджера резервного копирования
backup_manager = BackupManager()