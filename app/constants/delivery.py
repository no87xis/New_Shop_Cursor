"""
Константы для системы доставки
"""
from enum import Enum
from typing import Dict, List


class DeliveryOption(str, Enum):
    """Варианты доставки"""
    SELF_PICKUP_GROZNY = "SELF_PICKUP_GROZNY"
    COURIER_GROZNY = "COURIER_GROZNY"
    COURIER_MAK = "COURIER_MAK"
    COURIER_KHAS = "COURIER_KHAS"
    COURIER_OTHER = "COURIER_OTHER"


# Описания вариантов доставки
DELIVERY_DESCRIPTIONS: Dict[DeliveryOption, str] = {
    DeliveryOption.SELF_PICKUP_GROZNY: "Самовывоз (Склад, Грозный)",
    DeliveryOption.COURIER_GROZNY: "Доставка по Грозному",
    DeliveryOption.COURIER_MAK: "Доставка в Махачкалу",
    DeliveryOption.COURIER_KHAS: "Доставка в Хасавюрт",
    DeliveryOption.COURIER_OTHER: "Другая (по согласованию)"
}

# Варианты доставки с бесплатной доставкой
DELIVERY_OPTIONS_FREE: List[DeliveryOption] = [
    DeliveryOption.SELF_PICKUP_GROZNY
]

# Цена за единицу доставки в рублях
DELIVERY_UNIT_PRICE_RUB: int = 300


def calculate_delivery_cost(delivery_option: DeliveryOption, quantity: int) -> int:
    """
    Расчет стоимости доставки
    
    Args:
        delivery_option: Вариант доставки
        quantity: Количество товаров
        
    Returns:
        Стоимость доставки в рублях
    """
    if delivery_option in DELIVERY_OPTIONS_FREE:
        return 0
    return DELIVERY_UNIT_PRICE_RUB * quantity


def get_delivery_description(delivery_option: DeliveryOption) -> str:
    """
    Получение описания варианта доставки
    
    Args:
        delivery_option: Вариант доставки
        
    Returns:
        Описание доставки
    """
    return DELIVERY_DESCRIPTIONS.get(delivery_option, "Неизвестный вариант доставки")