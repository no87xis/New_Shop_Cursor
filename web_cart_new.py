"""
НОВАЯ КОРЗИНА - ПОЛНОСТЬЮ ПЕРЕПИСАННАЯ
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/cart/", response_class=HTMLResponse)
async def cart_page(request: Request):
    """
    НОВАЯ СТРАНИЦА КОРЗИНЫ - ПОЛНОСТЬЮ ПЕРЕПИСАННАЯ
    """
    try:
        # Создаем session_id если его нет
        session_id = request.session.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["session_id"] = session_id
            logger.info(f"Created new session: {session_id}")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Корзина - Sirius Group</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        .cart-item {{
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
        }}
        .error {{
            color: #ef4444;
            background: #fef2f2;
            border: 1px solid #fecaca;
            padding: 12px;
            border-radius: 6px;
            margin: 16px 0;
        }}
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-md">
        <div class="container mx-auto px-4 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <a href="/shop/" class="text-2xl font-bold text-blue-600">Sirius Group</a>
                    <span class="text-gray-400">|</span>
                    <h1 class="text-xl font-semibold">Корзина</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/shop/" class="text-gray-600 hover:text-blue-600">
                        <i class="fas fa-arrow-left mr-1"></i>
                        Продолжить покупки
                    </a>
                    <div class="relative">
                        <span class="bg-blue-600 text-white px-2 py-1 rounded-full text-sm" id="cart-count">0</span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <div class="container mx-auto px-4 py-8 max-w-6xl">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Cart Items -->
            <div class="lg:col-span-2">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-2xl font-bold text-gray-800 mb-6">
                        <i class="fas fa-shopping-cart mr-2"></i>
                        Товары в корзине
                    </h2>
                    
                    <div id="cart-items">
                        <div class="loading">
                            <div class="text-center">
                                <i class="fas fa-spinner fa-spin text-4xl text-blue-500 mb-4"></i>
                                <p class="text-gray-600">Загрузка корзины...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Order Summary -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-lg shadow-md p-6 sticky top-4">
                    <h3 class="text-xl font-bold text-gray-800 mb-4">Итого</h3>
                    
                    <div class="space-y-3 mb-6">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Товары:</span>
                            <span id="cart-total">0</span> ₽
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Доставка:</span>
                            <span class="text-gray-600">Рассчитывается при оформлении</span>
                        </div>
                        <div class="border-t pt-3">
                            <div class="flex justify-between text-lg font-bold">
                                <span>Итого:</span>
                                <span id="cart-total-final">0</span> ₽
                            </div>
                        </div>
                    </div>
                    
                    <button onclick="checkout()" 
                            class="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition duration-300 font-semibold">
                        <i class="fas fa-credit-card mr-2"></i>
                        Оформить заказ
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div id="toast-container" class="fixed top-4 right-4 z-50"></div>

    <!-- JavaScript -->
    <script>
        console.log('=== НОВАЯ КОРЗИНА ЗАГРУЖЕНА ===');
        console.log('Session ID: {session_id}');
        
        // Глобальные переменные
        let cartData = null;
        
        // Функция загрузки корзины
        async function loadCart() {{
            console.log('=== НАЧИНАЮ ЗАГРУЗКУ КОРЗИНЫ ===');
            
            try {{
                console.log('Отправляю запрос к API...');
                const response = await fetch("/api/shop/cart/items", {{
                    method: 'GET',
                    credentials: 'include',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }}
                }});
                
                console.log('Ответ получен, статус:', response.status);
                
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
                
                const data = await response.json();
                console.log('Данные корзины:', data);
                
                cartData = data;
                renderCart(data);
                
            }} catch (error) {{
                console.error('ОШИБКА ЗАГРУЗКИ КОРЗИНЫ:', error);
                showError('Ошибка загрузки корзины: ' + error.message);
            }}
        }}
        
        // Функция отображения корзины
        function renderCart(data) {{
            console.log('=== ОТОБРАЖАЮ КОРЗИНУ ===');
            console.log('Данные для отображения:', data);
            
            const container = document.getElementById("cart-items");
            const totalElement = document.getElementById("cart-total");
            const countElement = document.getElementById("cart-count");
            const totalFinalElement = document.getElementById("cart-total-final");
            
            if (!container) {{
                console.error('Контейнер cart-items не найден!');
                return;
            }}
            
            // Проверяем есть ли товары
            if (data && data.items && data.items.length > 0) {{
                console.log('Найдено товаров:', data.items.length);
                
                let html = '';
                data.items.forEach((item, index) => {{
                    console.log('Обрабатываю товар:', item);
                    
                    html += `
                        <div class="cart-item" data-product-id="${{item.product_id}}">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-4">
                                    <img src="${{item.photo_url || '/static/no-image.png'}}" 
                                         alt="${{item.product_name}}" 
                                         class="w-20 h-20 object-cover rounded-lg border">
                                    <div>
                                        <h3 class="font-semibold text-gray-800 text-lg">${{item.product_name}}</h3>
                                        <p class="text-sm text-gray-600">${{item.unit_price_rub.toLocaleString()}} ₽ за шт.</p>
                                        <p class="text-xs text-gray-500">ID: ${{item.product_id}}</p>
                                    </div>
                                </div>
                                <div class="flex items-center space-x-4">
                                    <div class="flex items-center space-x-2">
                                        <button onclick="updateQuantity(${{item.product_id}}, ${{item.quantity - 1}})" 
                                                class="bg-gray-200 text-gray-700 px-3 py-2 rounded hover:bg-gray-300 font-bold">
                                            -
                                        </button>
                                        <span class="px-4 py-2 bg-gray-100 rounded font-semibold min-w-[50px] text-center">
                                            ${{item.quantity}}
                                        </span>
                                        <button onclick="updateQuantity(${{item.product_id}}, ${{item.quantity + 1}})" 
                                                class="bg-gray-200 text-gray-700 px-3 py-2 rounded hover:bg-gray-300 font-bold">
                                            +
                                        </button>
                                    </div>
                                    <div class="text-right">
                                        <p class="font-bold text-xl text-blue-600">
                                            ${{item.total_price_rub.toLocaleString()}} ₽
                                        </p>
                                    </div>
                                    <button onclick="removeItem(${{item.product_id}})" 
                                            class="text-red-500 hover:text-red-700 p-2">
                                        <i class="fas fa-trash text-xl"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }});
                
                container.innerHTML = html;
                
                // Обновляем итоги
                if (totalElement) {{
                    totalElement.textContent = data.total_amount.toLocaleString();
                }}
                if (countElement) {{
                    countElement.textContent = data.count;
                }}
                if (totalFinalElement) {{
                    totalFinalElement.textContent = data.total_amount.toLocaleString();
                }}
                
                console.log('Корзина отображена успешно');
                
            }} else {{
                console.log('Корзина пуста');
                container.innerHTML = `
                    <div class="text-center py-12">
                        <i class="fas fa-shopping-cart text-8xl text-gray-300 mb-6"></i>
                        <h3 class="text-2xl font-semibold text-gray-600 mb-4">Корзина пуста</h3>
                        <p class="text-gray-500 mb-6">Добавьте товары в корзину, чтобы продолжить покупки</p>
                        <a href="/shop/" class="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition duration-300 text-lg font-semibold">
                            Перейти в магазин
                        </a>
                    </div>
                `;
                
                // Обнуляем итоги
                if (totalElement) totalElement.textContent = "0";
                if (countElement) countElement.textContent = "0";
                if (totalFinalElement) totalFinalElement.textContent = "0";
            }}
        }}
        
        // Функция обновления количества
        async function updateQuantity(productId, newQuantity) {{
            console.log('Обновляю количество для товара', productId, 'на', newQuantity);
            
            if (newQuantity < 0) {{
                console.log('Количество не может быть отрицательным');
                return;
            }}
            
            try {{
                const response = await fetch(`/api/shop/cart/update/${{productId}}?quantity=${{newQuantity}}`, {{
                    method: 'PUT',
                    credentials: 'include',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }});
                
                console.log('Ответ на обновление:', response.status);
                
                if (response.ok) {{
                    showToast('Количество обновлено', 'success');
                    loadCart(); // Перезагружаем корзину
                }} else {{
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Ошибка обновления');
                }}
            }} catch (error) {{
                console.error('Ошибка обновления количества:', error);
                showToast('Ошибка обновления количества: ' + error.message, 'error');
            }}
        }}
        
        // Функция удаления товара
        async function removeItem(productId) {{
            console.log('Удаляю товар', productId);
            
            if (!confirm('Удалить товар из корзины?')) {{
                return;
            }}
            
            try {{
                const response = await fetch(`/api/shop/cart/remove/${{productId}}`, {{
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }});
                
                console.log('Ответ на удаление:', response.status);
                
                if (response.ok) {{
                    showToast('Товар удален из корзины', 'success');
                    loadCart(); // Перезагружаем корзину
                }} else {{
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Ошибка удаления');
                }}
            }} catch (error) {{
                console.error('Ошибка удаления товара:', error);
                showToast('Ошибка удаления товара: ' + error.message, 'error');
            }}
        }}
        
        // Функция оформления заказа
        function checkout() {{
            if (!cartData || !cartData.items || cartData.items.length === 0) {{
                showToast('Корзина пуста', 'error');
                return;
            }}
            window.location.href = '/shop/checkout';
        }}
        
        // Функция показа ошибки
        function showError(message) {{
            const container = document.getElementById("cart-items");
            if (container) {{
                container.innerHTML = `
                    <div class="error">
                        <i class="fas fa-exclamation-triangle mr-2"></i>
                        ${{message}}
                        <button onclick="loadCart()" class="ml-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                            Попробовать снова
                        </button>
                    </div>
                `;
            }}
        }}
        
        // Функция показа уведомлений
        function showToast(message, type) {{
            const container = document.getElementById('toast-container');
            if (!container) return;
            
            const toast = document.createElement('div');
            const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
            
            toast.className = bgColor + ' text-white px-6 py-3 rounded-lg shadow-lg mb-2 transform transition-all duration-300 translate-x-full';
            
            toast.innerHTML = `
                <div class="flex items-center">
                    <span class="mr-2">${{message}}</span>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            container.appendChild(toast);
            
            setTimeout(() => {{
                toast.classList.remove('translate-x-full');
            }}, 100);
            
            setTimeout(() => {{
                toast.classList.add('translate-x-full');
                setTimeout(() => {{
                    if (toast.parentElement) {{
                        toast.remove();
                    }}
                }}, 300);
            }}, 3000);
        }}
        
        // Загружаем корзину при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('=== DOM ЗАГРУЖЕН, НАЧИНАЮ ЗАГРУЗКУ КОРЗИНЫ ===');
            loadCart();
        }});
        
        // Дополнительная загрузка через 1 секунду (на всякий случай)
        setTimeout(() => {{
            console.log('=== ДОПОЛНИТЕЛЬНАЯ ЗАГРУЗКА КОРЗИНЫ ===');
            loadCart();
        }}, 1000);
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Error loading cart page: {e}")
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
                <p class="text-sm text-gray-500 mt-2">Ошибка: {e}</p>
            </div>
        </body>
        </html>
        """)