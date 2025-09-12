"""
Простая админка без шаблонов
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Простая панель администратора
    """
    try:
        # Получаем статистику
        total_products = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
        total_orders = db.execute(text("SELECT COUNT(*) FROM shop_orders")).scalar()
        total_cart_items = db.execute(text("SELECT COUNT(*) FROM shop_carts")).scalar()
        
        # Общая сумма заказов
        total_amount_result = db.execute(text("SELECT SUM(total_amount) FROM shop_orders WHERE total_amount IS NOT NULL")).scalar()
        total_amount = float(total_amount_result) if total_amount_result else 0.0
        
        # Последние заказы
        recent_orders = db.execute(text("""
            SELECT id, order_code, customer_name, customer_phone, total_amount, status, created_at 
            FROM shop_orders 
            ORDER BY created_at DESC 
            LIMIT 10
        """)).fetchall()
        
        # Товары с низким остатком
        low_stock_products = db.execute(text("""
            SELECT id, name, quantity, min_stock 
            FROM products 
            WHERE quantity <= min_stock AND availability_status = 'IN_STOCK'
            ORDER BY quantity ASC
        """)).fetchall()
        
        # Все товары
        all_products = db.execute(text("""
            SELECT id, name, sell_price_rub, quantity, availability_status, created_at
            FROM products 
            ORDER BY created_at DESC
        """)).fetchall()
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ панель - Sirius Group</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-100 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-md">
        <div class="container mx-auto px-4 py-4">
            <div class="flex items-center justify-between">
                <h1 class="text-2xl font-bold text-blue-600">
                    <i class="fas fa-cog mr-2"></i>
                    Админ панель
                </h1>
                <div class="flex space-x-4">
                    <a href="/shop/" class="text-gray-600 hover:text-blue-600">
                        <i class="fas fa-store mr-1"></i>
                        Магазин
                    </a>
                    <a href="/cart/" class="text-gray-600 hover:text-blue-600">
                        <i class="fas fa-shopping-cart mr-1"></i>
                        Корзина
                    </a>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <div class="container mx-auto px-4 py-8 max-w-7xl">
        <!-- Статистика -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-blue-100 text-blue-600">
                        <i class="fas fa-box text-2xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Товары</p>
                        <p class="text-2xl font-bold text-gray-900">{total_products}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-green-100 text-green-600">
                        <i class="fas fa-shopping-bag text-2xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Заказы</p>
                        <p class="text-2xl font-bold text-gray-900">{total_orders}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
                        <i class="fas fa-shopping-cart text-2xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">В корзинах</p>
                        <p class="text-2xl font-bold text-gray-900">{total_cart_items}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-purple-100 text-purple-600">
                        <i class="fas fa-ruble-sign text-2xl"></i>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Общая сумма</p>
                        <p class="text-2xl font-bold text-gray-900">{total_amount:,.0f}₽</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- Последние заказы -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-clock mr-2"></i>
                    Последние заказы
                </h2>
                <div class="space-y-3">
                    {''.join([f'''
                    <div class="border-l-4 border-blue-500 pl-4 py-2">
                        <div class="flex justify-between items-start">
                            <div>
                                <p class="font-semibold text-gray-800">#{order[1] or 'N/A'}</p>
                                <p class="text-sm text-gray-600">{order[2] or 'Без имени'}</p>
                                <p class="text-xs text-gray-500">{order[6].strftime('%d.%m.%Y %H:%M') if order[6] else 'N/A'}</p>
                            </div>
                            <div class="text-right">
                                <p class="font-bold text-green-600">{order[4]:,.0f}₽</p>
                                <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">{order[5] or 'NEW'}</span>
                            </div>
                        </div>
                    </div>
                    ''' for order in recent_orders]) if recent_orders else '<p class="text-gray-500">Заказов пока нет</p>'}
                </div>
            </div>

            <!-- Товары с низким остатком -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold text-gray-800 mb-4">
                    <i class="fas fa-exclamation-triangle mr-2 text-yellow-500"></i>
                    Низкий остаток
                </h2>
                <div class="space-y-3">
                    {''.join([f'''
                    <div class="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                        <div>
                            <p class="font-semibold text-gray-800">{product[1]}</p>
                            <p class="text-sm text-gray-600">Остаток: {product[2]} (мин: {product[3]})</p>
                        </div>
                        <span class="px-2 py-1 text-xs rounded-full bg-yellow-200 text-yellow-800">
                            {product[2]} шт
                        </span>
                    </div>
                    ''' for product in low_stock_products]) if low_stock_products else '<p class="text-gray-500">Все товары в наличии</p>'}
                </div>
            </div>
        </div>

        <!-- Все товары -->
        <div class="mt-8 bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-bold text-gray-800 mb-4">
                <i class="fas fa-list mr-2"></i>
                Все товары
            </h2>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Название</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Цена</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Остаток</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Создан</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {''.join([f'''
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product[0]}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product[1]}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product[2]:,.0f}₽</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product[3]}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full {'bg-green-100 text-green-800' if product[4] == 'IN_STOCK' else 'bg-red-100 text-red-800'}">
                                    {product[4]}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {product[5].strftime('%d.%m.%Y') if product[5] else 'N/A'}
                            </td>
                        </tr>
                        ''' for product in all_products]) if all_products else '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">Товаров нет</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Ошибка админки</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center">
            <div class="bg-white p-8 rounded-lg shadow-md text-center">
                <h1 class="text-2xl font-bold text-red-600 mb-4">Ошибка админки</h1>
                <p class="text-gray-600">Ошибка: {e}</p>
            </div>
        </body>
        </html>
        """)