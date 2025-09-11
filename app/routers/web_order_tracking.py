"""
Веб-страницы для отслеживания заказов
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.qr_service import QRCodeService
from app.models.shop_order import ShopOrder
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/shop/o/{qr_token}", response_class=HTMLResponse)
async def track_order_page(request: Request, qr_token: str, db: Session = Depends(get_db)):
    """
    Публичная страница отслеживания заказа по QR-коду
    """
    try:
        order = QRCodeService.get_order_by_qr_token(db, qr_token)
        
        if not order:
            return HTMLResponse("""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Заказ не найден</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 min-h-screen flex items-center justify-center">
                <div class="bg-white p-8 rounded-lg shadow-md text-center">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">Заказ не найден</h1>
                    <p class="text-gray-600">Проверьте правильность QR-кода</p>
                </div>
            </body>
            </html>
            """)
        
        # Определяем цвет статуса
        status_colors = {
            "ordered_not_paid": "bg-yellow-100 text-yellow-800",
            "paid_not_issued": "bg-blue-100 text-blue-800", 
            "paid_issued": "bg-green-100 text-green-800",
            "cancelled": "bg-red-100 text-red-800"
        }
        
        status_texts = {
            "ordered_not_paid": "Ожидает оплаты",
            "paid_not_issued": "Оплачен, готовится к выдаче",
            "paid_issued": "Выдан",
            "cancelled": "Отменен"
        }
        
        status_color = status_colors.get(order.status, "bg-gray-100 text-gray-800")
        status_text = status_texts.get(order.status, order.status)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Отслеживание заказа {order.order_code}</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8 max-w-4xl">
                <!-- Заголовок -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div class="flex items-center justify-between mb-4">
                        <h1 class="text-3xl font-bold text-gray-800">Заказ #{order.order_code}</h1>
                        <span class="px-4 py-2 rounded-full text-sm font-medium {status_color}">
                            {status_text}
                        </span>
                    </div>
                    <p class="text-gray-600">Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}</p>
                </div>

                <!-- Информация о клиенте -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 class="text-xl font-semibold text-gray-800 mb-4">
                        <i class="fas fa-user mr-2"></i>Информация о клиенте
                    </h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <p class="text-sm text-gray-600">Имя</p>
                            <p class="font-medium">{order.customer_name}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Телефон</p>
                            <p class="font-medium">{order.customer_phone}</p>
                        </div>
                    </div>
                </div>

                <!-- Информация о доставке -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 class="text-xl font-semibold text-gray-800 mb-4">
                        <i class="fas fa-truck mr-2"></i>Доставка
                    </h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <p class="text-sm text-gray-600">Способ доставки</p>
                            <p class="font-medium">{order.delivery_option}</p>
                        </div>
                        <div>
                            <p class="text-sm text-gray-600">Адрес</p>
                            <p class="font-medium">{order.delivery_address}</p>
                        </div>
                    </div>
                </div>

                <!-- Товары в заказе -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                    <h2 class="text-xl font-semibold text-gray-800 mb-4">
                        <i class="fas fa-shopping-cart mr-2"></i>Товары в заказе
                    </h2>
                    <div class="space-y-4">
        """
        
        # Добавляем товары
        for item in order.order_items:
            html_content += f"""
                        <div class="flex items-center justify-between p-4 border rounded-lg">
                            <div class="flex-1">
                                <h3 class="font-medium text-gray-800">{item.product.name}</h3>
                                <p class="text-sm text-gray-600">Количество: {item.quantity} шт.</p>
                            </div>
                            <div class="text-right">
                                <p class="font-medium">{item.unit_price_rub:,.0f} ₽ за шт.</p>
                                <p class="text-lg font-bold text-blue-600">{(item.quantity * item.unit_price_rub):,.0f} ₽</p>
                            </div>
                        </div>
            """
        
        html_content += f"""
                    </div>
                </div>

                <!-- Стоимость заказа -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold text-gray-800 mb-4">
                        <i class="fas fa-calculator mr-2"></i>Стоимость заказа
                    </h2>
                    <div class="space-y-2">
                        <div class="flex justify-between">
                            <span>Товары:</span>
                            <span>{(order.total_amount - order.delivery_cost_rub):,.0f} ₽</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Доставка:</span>
                            <span>{order.delivery_cost_rub:,.0f} ₽</span>
                        </div>
                        <div class="flex justify-between text-lg font-bold border-t pt-2">
                            <span>Итого:</span>
                            <span class="text-blue-600">{order.total_amount:,.0f} ₽</span>
                        </div>
                    </div>
                </div>

                <!-- Кнопка обновления -->
                <div class="text-center mt-6">
                    <button onclick="location.reload()" 
                            class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-300">
                        <i class="fas fa-sync-alt mr-2"></i>Обновить статус
                    </button>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(html_content)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы отслеживания: {e}")
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Ошибка</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center">
            <div class="bg-white p-8 rounded-lg shadow-md text-center">
                <h1 class="text-2xl font-bold text-red-600 mb-4">Ошибка загрузки</h1>
                <p class="text-gray-600">Попробуйте обновить страницу</p>
            </div>
        </body>
        </html>
        """)