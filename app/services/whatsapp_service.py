"""
Сервис для WhatsApp уведомлений
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from app.config import settings
from app.schemas.notification import (
    NotificationSendRequest, 
    NotificationSendResponse,
    RecipientData
)
from app.constants.notifications import (
    MESSAGE_TEMPLATES,
    NOTIFICATION_STATUSES,
    get_template_variables,
    validate_template_variables
)

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Сервис для отправки WhatsApp уведомлений"""
    
    def __init__(self):
        self.relay_url = settings.whatsapp_relay_url
        self.relay_token = settings.whatsapp_relay_token
        self.rate_limit_per_minute = settings.whatsapp_rate_limit_per_min
        self.min_delay_ms = settings.whatsapp_send_delay_min_ms
        self.max_delay_ms = settings.whatsapp_send_delay_max_ms
        self.dry_run_enabled = settings.whatsapp_dry_run_enabled
        self.test_mode = settings.whatsapp_test_mode
        self.test_phone = settings.whatsapp_test_phone
    
    async def send_notifications(self, request: NotificationSendRequest) -> NotificationSendResponse:
        """
        Отправка уведомлений
        
        Args:
            request: Запрос на отправку уведомлений
            
        Returns:
            Ответ с результатами отправки
        """
        try:
            batch_id = request.batch_id or str(uuid.uuid4())
            results = []
            
            # Валидация шаблона
            if not validate_template_variables(request.template_key, request.template_vars):
                raise ValueError(f"Invalid template variables for {request.template_key}")
            
            # Получаем шаблон
            template = MESSAGE_TEMPLATES.get(request.template_key)
            if not template:
                raise ValueError(f"Template {request.template_key} not found")
            
            # Обрабатываем получателей батчами
            for i in range(0, len(request.recipients), request.rate.get("batch_size", 10)):
                batch = request.recipients[i:i + request.rate.get("batch_size", 10)]
                
                # Отправляем батч
                batch_results = await self._send_batch(
                    batch, 
                    template, 
                    request.template_vars, 
                    request.message_override,
                    request.dry_run or self.dry_run_enabled,
                    batch_id
                )
                
                results.extend(batch_results)
                
                # Задержка между батчами
                if i + request.rate.get("batch_size", 10) < len(request.recipients):
                    await asyncio.sleep(request.rate.get("batch_delay_ms", 1000) / 1000)
            
            # Подсчитываем результаты
            total_sent = sum(1 for r in results if r["status"] == "sent")
            total_failed = sum(1 for r in results if r["status"] == "fail")
            total_skipped = sum(1 for r in results if r["status"] == "skipped")
            total_invalid = sum(1 for r in results if r["status"] == "invalid_phone")
            
            return NotificationSendResponse(
                ok=total_failed == 0,
                dry_run=request.dry_run or self.dry_run_enabled,
                batch_id=batch_id,
                results=results,
                total_sent=total_sent,
                total_failed=total_failed,
                total_skipped=total_skipped,
                total_invalid=total_invalid
            )
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            raise
    
    async def _send_batch(
        self, 
        recipients: List[RecipientData], 
        template: Dict[str, str], 
        template_vars: Dict[str, str],
        message_override: Optional[str],
        dry_run: bool,
        batch_id: str
    ) -> List[Dict[str, Any]]:
        """
        Отправка батча уведомлений
        
        Args:
            recipients: Список получателей
            template: Шаблон сообщения
            template_vars: Переменные шаблона
            message_override: Переопределение сообщения
            dry_run: Режим тестирования
            batch_id: ID батча
            
        Returns:
            Список результатов отправки
        """
        results = []
        
        for recipient in recipients:
            try:
                # Нормализуем номер телефона
                normalized_phone = self._normalize_phone(recipient.phone)
                if not normalized_phone:
                    results.append({
                        "recipient": recipient.dict(),
                        "status": "invalid_phone",
                        "error": "Invalid phone number format",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                # Генерируем сообщение
                message_text = self._generate_message(
                    template, 
                    template_vars, 
                    recipient, 
                    message_override
                )
                
                if dry_run:
                    # Режим тестирования
                    results.append({
                        "recipient": recipient.dict(),
                        "status": "sent",
                        "message_text": message_text,
                        "wa_message_id": f"dry_run_{uuid.uuid4()}",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Отправляем через WhatsApp Relay
                    result = await self._send_single_message(
                        normalized_phone, 
                        message_text, 
                        recipient
                    )
                    results.append(result)
                
                # Задержка между сообщениями
                delay = self._calculate_delay()
                await asyncio.sleep(delay / 1000)
                
            except Exception as e:
                logger.error(f"Error sending message to {recipient.phone}: {e}")
                results.append({
                    "recipient": recipient.dict(),
                    "status": "fail",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return results
    
    async def _send_single_message(
        self, 
        phone: str, 
        message: str, 
        recipient: RecipientData
    ) -> Dict[str, Any]:
        """
        Отправка одного сообщения через WhatsApp Relay
        
        Args:
            phone: Номер телефона
            message: Текст сообщения
            recipient: Данные получателя
            
        Returns:
            Результат отправки
        """
        try:
            # В тестовом режиме отправляем на тестовый номер
            if self.test_mode:
                phone = self.test_phone
            
            # Подготавливаем данные для отправки
            payload = {
                "phone": phone,
                "message": message,
                "recipient_data": recipient.dict()
            }
            
            # Отправляем через WhatsApp Relay
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.relay_url}/wa/send",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.relay_token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "recipient": recipient.dict(),
                        "status": "sent",
                        "message_text": message,
                        "wa_message_id": data.get("message_id"),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = f"HTTP {response.status_code}: {response.text}"
                    return {
                        "recipient": recipient.dict(),
                        "status": "fail",
                        "error": error_text,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Error sending single message: {e}")
            return {
                "recipient": recipient.dict(),
                "status": "fail",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """
        Нормализация номера телефона
        
        Args:
            phone: Исходный номер телефона
            
        Returns:
            Нормализованный номер или None
        """
        try:
            import phonenumbers
            
            # Убираем все нецифровые символы кроме +
            cleaned = phone.strip()
            
            # Парсим номер
            parsed = phonenumbers.parse(cleaned, settings.default_country_code)
            
            # Проверяем валидность
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error normalizing phone {phone}: {e}")
            return None
    
    def _generate_message(
        self, 
        template: Dict[str, str], 
        template_vars: Dict[str, str], 
        recipient: RecipientData,
        message_override: Optional[str]
    ) -> str:
        """
        Генерация текста сообщения
        
        Args:
            template: Шаблон сообщения
            template_vars: Переменные шаблона
            recipient: Данные получателя
            message_override: Переопределение сообщения
            
        Returns:
            Сгенерированный текст сообщения
        """
        try:
            if message_override:
                return message_override
            
            template_text = template.get("template", "")
            
            # Подготавливаем переменные
            variables = {
                "name": recipient.name,
                "orderId": recipient.orderId or "",
                "pickup_address": template_vars.get("pickup_address", settings.pickup_address),
                "pickup_hours": template_vars.get("pickup_hours", settings.pickup_hours),
                **template_vars
            }
            
            # Заменяем переменные в шаблоне
            message = template_text
            for key, value in variables.items():
                # Обрабатываем условные переменные (например, {orderId? ' №'+orderId : ''})
                if "?" in key:
                    var_name = key.split("?")[0]
                    if var_name in variables and variables[var_name]:
                        # Если переменная есть и не пустая, используем значение после ?
                        condition_part = key.split("?")[1]
                        if ":" in condition_part:
                            true_value = condition_part.split(":")[0].strip()
                            message = message.replace(f"{{{key}}}", true_value)
                        else:
                            message = message.replace(f"{{{key}}}", str(variables[var_name]))
                    else:
                        # Если переменной нет или она пустая, используем значение после :
                        if ":" in key:
                            false_value = key.split(":")[1].strip()
                            message = message.replace(f"{{{key}}}", false_value)
                        else:
                            message = message.replace(f"{{{key}}}", "")
                else:
                    # Обычная замена переменной
                    message = message.replace(f"{{{key}}}", str(value))
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating message: {e}")
            return template.get("template", "")
    
    def _calculate_delay(self) -> int:
        """
        Расчет задержки между сообщениями
        
        Returns:
            Задержка в миллисекундах
        """
        import random
        return random.randint(self.min_delay_ms, self.max_delay_ms)
    
    async def check_relay_health(self) -> bool:
        """
        Проверка здоровья WhatsApp Relay
        
        Returns:
            True если Relay работает
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.relay_url}/wa/health",
                    headers={"Authorization": f"Bearer {self.relay_token}"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("ok", False) and data.get("clientReady", False)
                else:
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking relay health: {e}")
            return False
    
    def get_available_templates(self) -> List[Dict[str, str]]:
        """
        Получение доступных шаблонов
        
        Returns:
            Список доступных шаблонов
        """
        try:
            templates = []
            for key, template in MESSAGE_TEMPLATES.items():
                templates.append({
                    "key": key,
                    "name": template.get("name", ""),
                    "description": template.get("description", ""),
                    "variables": get_template_variables(key)
                })
            return templates
        except Exception as e:
            logger.error(f"Error getting available templates: {e}")
            return []
    
    def preview_message(
        self, 
        template_key: str, 
        template_vars: Dict[str, str], 
        recipient: RecipientData
    ) -> str:
        """
        Превью сообщения
        
        Args:
            template_key: Ключ шаблона
            template_vars: Переменные шаблона
            recipient: Данные получателя
            
        Returns:
            Превью сообщения
        """
        try:
            template = MESSAGE_TEMPLATES.get(template_key)
            if not template:
                return "Template not found"
            
            return self._generate_message(template, template_vars, recipient, None)
            
        except Exception as e:
            logger.error(f"Error previewing message: {e}")
            return "Error generating preview"


# Глобальный экземпляр сервиса
whatsapp_service = WhatsAppService()