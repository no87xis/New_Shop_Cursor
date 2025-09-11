"""
Веб-страница корзины
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/cart/", response_class=HTMLResponse)
async def cart_page(request: Request):
    """
    Страница корзины
    """
    try:
        html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Корзина - Sirius Group</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
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
                    
                    <div class="space-y-4" id="cart-items">
                        <!-- Товары будут загружены через JavaScript -->
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
        async function loadCart() {
            try {
                const response = await fetch("/api/shop/cart/items");
                const data = await response.json();
                
                const container = document.getElementById("cart-items");
                const totalElement = document.getElementById("cart-total");
                const countElement = document.getElementById("cart-count");
                const totalFinalElement = document.getElementById("cart-total-final");
                
                if (data.success && data.items && data.items.length > 0) {
                    container.innerHTML = data.items.map(item => `
                        <div class="bg-white rounded-lg shadow-md p-4 flex items-center justify-between">
                            <div class="flex items-center space-x-4">
                                <img src="${item.photo_url}" alt="${item.product_name}" class="w-16 h-16 object-cover rounded-lg">
                                <div>
                                    <h3 class="font-semibold text-gray-800">${item.product_name}</h3>
                                    <p class="text-sm text-gray-600">${item.unit_price_rub.toLocaleString()} ₽ за шт.</p>
                                </div>
                            </div>
                            <div class="flex items-center space-x-4">
                                <div class="flex items-center space-x-2">
                                    <button onclick="updateQuantity(${item.product_id}, ${item.quantity - 1})" class="bg-gray-200 text-gray-700 px-2 py-1 rounded hover:bg-gray-300">-</button>
                                    <span class="px-3 py-1 bg-gray-100 rounded">${item.quantity}</span>
                                    <button onclick="updateQuantity(${item.product_id}, ${item.quantity + 1})" class="bg-gray-200 text-gray-700 px-2 py-1 rounded hover:bg-gray-300">+</button>
                                </div>
                                <div class="text-right">
                                    <p class="font-semibold text-lg">${item.total_price_rub.toLocaleString()} ₽</p>
                                </div>
                                <button onclick="removeItem(${item.product_id})" class="text-red-500 hover:text-red-700">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `).join("");
                    
                    if (totalElement) {
                        totalElement.textContent = data.total_amount.toLocaleString();
                    }
                    if (countElement) {
                        countElement.textContent = data.count;
                    }
                    if (totalFinalElement) {
                        totalFinalElement.textContent = data.total_amount.toLocaleString();
                    }
                } else {
                    container.innerHTML = `
                        <div class="text-center py-8">
                            <i class="fas fa-shopping-cart text-6xl text-gray-300 mb-4"></i>
                            <h3 class="text-xl font-semibold text-gray-600 mb-2">Корзина пуста</h3>
                            <p class="text-gray-500 mb-4">Добавьте товары в корзину, чтобы продолжить покупки</p>
                            <a href="/shop/" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-300">Перейти в магазин</a>
                        </div>
                    `;
                    
                    if (totalElement) {
                        totalElement.textContent = "0";
                    }
                    if (countElement) {
                        countElement.textContent = "0";
                    }
                    if (totalFinalElement) {
                        totalFinalElement.textContent = "0";
                    }
                }
            } catch (error) {
                console.error("Error loading cart:", error);
                showToast("Ошибка загрузки корзины", "error");
            }
        }

        async function updateQuantity(productId, newQuantity) {
            if (newQuantity < 0) return;
            
            try {
                const response = await fetch(`/api/shop/cart/update/${productId}?quantity=${newQuantity}`, {
                    method: 'PUT'
                });
                
                if (response.ok) {
                    loadCart(); // Перезагружаем корзину
                    showToast('Количество обновлено', 'success');
                } else {
                    showToast('Ошибка обновления количества', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showToast('Ошибка обновления количества', 'error');
            }
        }

        async function removeItem(productId) {
            try {
                const response = await fetch(`/api/shop/cart/remove/${productId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    loadCart(); // Перезагружаем корзину
                    showToast('Товар удален из корзины', 'success');
                } else {
                    showToast('Ошибка удаления товара', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showToast('Ошибка удаления товара', 'error');
            }
        }

        function checkout() {
            window.location.href = '/shop/checkout';
        }

        function showToast(message, type) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            
            const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
            
            toast.className = bgColor + ' text-white px-6 py-3 rounded-lg shadow-lg mb-2 transform transition-all duration-300 translate-x-full';
            
            toast.innerHTML = '<div class="flex items-center"><span class="mr-2">' + message + '</span><button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200"><i class="fas fa-times"></i></button></div>';
            
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.classList.remove('translate-x-full');
            }, 100);
            
            setTimeout(() => {
                toast.classList.add('translate-x-full');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 300);
            }, 3000);
        }

        // Загружаем корзину при загрузке страницы
        document.addEventListener('DOMContentLoaded', loadCart);
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
            </div>
        </body>
        </html>
        """)