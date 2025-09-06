"""
Константы для системы уведомлений - НОВОЕ
"""
from typing import Dict, List


# Шаблоны сообщений
MESSAGE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "arrived_v1": {
        "name": "Уведомление о прибытии товара",
        "template": "{name}, ваш заказ{orderId? ' №'+orderId : ''} приехал и готов к выдаче.\n📍 Пункт выдачи: {pickup_address}\n🕒 Время: {pickup_hours}\nЕсли неудобно — напишите, согласуем время.",
        "description": "Уведомление клиенту о том, что заказ прибыл на склад и готов к выдаче"
    },
    "ready_v1": {
        "name": "Уведомление о готовности к выдаче",
        "template": "{name}, ваш заказ{orderId? ' №'+orderId : ''} готов к выдаче.\n📍 Пункт выдачи: {pickup_address}\n🕒 Время: {pickup_hours}",
        "description": "Уведомление о готовности заказа к выдаче"
    },
    "shipped_v1": {
        "name": "Уведомление об отправке",
        "template": "{name}, ваш заказ{orderId? ' №'+orderId : ''} отправлен.\n🚚 Трек-номер: {tracking_number}\n📅 Ожидаемая доставка: {delivery_date}",
        "description": "Уведомление об отправке заказа"
    }
}

# Статусы уведомлений
NOTIFICATION_STATUSES = {
    "SENT": "sent",
    "FAILED": "fail", 
    "SKIPPED": "skipped",
    "INVALID_PHONE": "invalid_phone"
}

# Статусы прибытия заказов
ARRIVAL_STATUSES = {
    "PENDING": "pending",
    "NOTIFIED": "notified", 
    "FAILED": "failed"
}

# Настройки WhatsApp Relay
WHATSAPP_RELAY_SETTINGS = {
    "RATE_LIMIT_PER_MINUTE": 45,
    "MIN_DELAY_MS": 900,
    "MAX_DELAY_MS": 1700,
    "MAX_RECIPIENTS_PER_BATCH": 50,
    "DEFAULT_COUNTRY": "BY"
}

# Коды стран для нормализации телефонов
COUNTRY_CODES = {
    "BY": "+375",
    "RU": "+7", 
    "UA": "+380"
}

# Настройки по умолчанию
DEFAULT_PICKUP_ADDRESS = "Наш склад, ул. Примерная, 123"
DEFAULT_PICKUP_HOURS = "Пн-Пт: 10:00-19:00, Сб: 10:00-16:00"
DEFAULT_COUNTRY_CODE = "BY"

# Лимиты и ограничения
NOTIFICATION_LIMITS = {
    "MAX_RECIPIENTS_PER_REQUEST": 50,
    "MAX_MESSAGE_LENGTH": 1000,
    "MAX_RETRY_ATTEMPTS": 3,
    "RETRY_DELAY_MS": 5000
}

# Переменные шаблонов
TEMPLATE_VARIABLES = {
    "name": "Имя клиента",
    "orderId": "Номер заказа",
    "pickup_address": "Адрес пункта выдачи",
    "pickup_hours": "Часы работы",
    "tracking_number": "Трек-номер",
    "delivery_date": "Дата доставки"
}


def get_template_variables(template_key: str) -> List[str]:
    """
    Получение переменных для шаблона
    
    Args:
        template_key: Ключ шаблона
        
    Returns:
        Список переменных шаблона
    """
    template = MESSAGE_TEMPLATES.get(template_key, {})
    template_text = template.get("template", "")
    
    # Извлекаем переменные из шаблона
    import re
    variables = re.findall(r'\{([^}]+)\}', template_text)
    
    # Убираем условия и оставляем только имена переменных
    clean_variables = []
    for var in variables:
        if '?' in var:
            var = var.split('?')[0]
        clean_variables.append(var)
    
    return list(set(clean_variables))


def validate_template_variables(template_key: str, template_vars: Dict[str, str]) -> bool:
    """
    Валидация переменных шаблона
    
    Args:
        template_key: Ключ шаблона
        template_vars: Переменные шаблона
        
    Returns:
        True если все переменные валидны
    """
    required_vars = get_template_variables(template_key)
    
    for var in required_vars:
        if var not in template_vars:
            return False
    
    return True