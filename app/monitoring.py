"""
Система мониторинга Sirius Group V2
"""
import logging
import traceback
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SystemMetrics:
    """Метрики системы"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    timestamp: datetime
    uptime: float


@dataclass
class ErrorInfo:
    """Информация об ошибке"""
    timestamp: datetime
    error: str
    context: str
    traceback: str
    level: LogLevel


class SystemMonitor:
    """Мониторинг состояния системы"""
    
    def __init__(self):
        self.errors: List[ErrorInfo] = []
        self.warnings: List[str] = []
        self.metrics_history: List[SystemMetrics] = []
        self.status = "unknown"
        self.start_time = time.time()
        
        # Настройка логирования
        self._setup_logging()
    
    def _setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/monitoring.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error: Exception, context: str = ""):
        """Логирует ошибку"""
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            error=str(error),
            context=context,
            traceback=traceback.format_exc(),
            level=LogLevel.ERROR
        )
        self.errors.append(error_info)
        self.logger.error(f"Error in {context}: {error}")
    
    def log_warning(self, message: str, context: str = ""):
        """Логирует предупреждение"""
        warning_info = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context
        }
        self.warnings.append(warning_info)
        self.logger.warning(f"Warning in {context}: {message}")
    
    def log_info(self, message: str, context: str = ""):
        """Логирует информационное сообщение"""
        self.logger.info(f"Info in {context}: {message}")
    
    def collect_metrics(self) -> SystemMetrics:
        """Сбор метрик системы"""
        try:
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_percent=psutil.disk_usage('/').percent,
                timestamp=datetime.now(),
                uptime=time.time() - self.start_time
            )
            
            self.metrics_history.append(metrics)
            
            # Ограничиваем историю метрик
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
            
            return metrics
            
        except Exception as e:
            self.log_error(e, "collect_metrics")
            return None
    
    def check_system_health(self) -> Dict[str, Any]:
        """Проверяет здоровье системы"""
        try:
            # Собираем текущие метрики
            current_metrics = self.collect_metrics()
            
            health = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time,
                "errors_count": len(self.errors),
                "warnings_count": len(self.warnings),
                "last_error": self.errors[-1].__dict__ if self.errors else None,
                "metrics": current_metrics.__dict__ if current_metrics else None
            }
            
            # Определяем статус на основе метрик и ошибок
            if len(self.errors) > 10:
                health["status"] = "critical"
            elif len(self.errors) > 5:
                health["status"] = "warning"
            elif current_metrics:
                if (current_metrics.cpu_percent > 90 or 
                    current_metrics.memory_percent > 90 or 
                    current_metrics.disk_percent > 90):
                    health["status"] = "warning"
            
            self.status = health["status"]
            return health
            
        except Exception as e:
            self.log_error(e, "check_system_health")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Получение сводки производительности"""
        try:
            if not self.metrics_history:
                return {"message": "No metrics available"}
            
            # Статистика по метрикам
            cpu_values = [m.cpu_percent for m in self.metrics_history]
            memory_values = [m.memory_percent for m in self.metrics_history]
            disk_values = [m.disk_percent for m in self.metrics_history]
            
            summary = {
                "period": {
                    "start": self.metrics_history[0].timestamp.isoformat(),
                    "end": self.metrics_history[-1].timestamp.isoformat(),
                    "duration_minutes": (self.metrics_history[-1].timestamp - self.metrics_history[0].timestamp).total_seconds() / 60
                },
                "cpu": {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "avg": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values)
                },
                "disk": {
                    "avg": sum(disk_values) / len(disk_values),
                    "max": max(disk_values),
                    "min": min(disk_values)
                },
                "errors_count": len(self.errors),
                "warnings_count": len(self.warnings)
            }
            
            return summary
            
        except Exception as e:
            self.log_error(e, "get_performance_summary")
            return {"error": str(e)}
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних ошибок"""
        try:
            recent_errors = self.errors[-limit:] if self.errors else []
            return [error.__dict__ for error in recent_errors]
        except Exception as e:
            self.log_error(e, "get_recent_errors")
            return []
    
    def get_recent_warnings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних предупреждений"""
        try:
            return self.warnings[-limit:] if self.warnings else []
        except Exception as e:
            self.log_error(e, "get_recent_warnings")
            return []
    
    def clear_old_data(self, days: int = 7):
        """Очистка старых данных"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            # Очищаем старые ошибки
            self.errors = [
                error for error in self.errors 
                if error.timestamp.timestamp() > cutoff_time
            ]
            
            # Очищаем старые предупреждения
            self.warnings = [
                warning for warning in self.warnings 
                if warning.get('timestamp', '') and 
                datetime.fromisoformat(warning['timestamp']).timestamp() > cutoff_time
            ]
            
            self.logger.info(f"Cleared data older than {days} days")
            
        except Exception as e:
            self.log_error(e, "clear_old_data")
    
    def export_metrics(self, format: str = "json") -> str:
        """Экспорт метрик в файл"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/metrics_export_{timestamp}.{format}"
            
            if format == "json":
                import json
                data = {
                    "export_time": datetime.now().isoformat(),
                    "metrics": [m.__dict__ for m in self.metrics_history],
                    "errors": [e.__dict__ for e in self.errors],
                    "warnings": self.warnings
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Metrics exported to {filename}")
            return filename
            
        except Exception as e:
            self.log_error(e, "export_metrics")
            return None


# Глобальный экземпляр монитора
monitor = SystemMonitor()


def monitor_function(func):
    """Декоратор для мониторинга функций"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            monitor.log_info(f"Function {func.__name__} executed successfully in {execution_time:.2f}s", func.__name__)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            monitor.log_error(e, f"{func.__name__} (execution_time: {execution_time:.2f}s)")
            raise
    return wrapper


def get_system_status() -> Dict[str, Any]:
    """Получение статуса системы"""
    return monitor.check_system_health()


def get_performance_metrics() -> Dict[str, Any]:
    """Получение метрик производительности"""
    return monitor.get_performance_summary()