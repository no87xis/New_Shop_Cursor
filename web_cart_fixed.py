from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.shop_cart_service import ShopCartService
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.get("/shop/cart", response_class=HTMLResponse)
async def cart_page(request: Request, db: Session = Depends(get_db)):
    try:
        session_id = get_session_id(request)
        cart_service = ShopCartService(db)
        
        cart_items = cart_service.get_cart_items(session_id)
        
        items_data = []
        total_amount = 0
        
        for item in cart_items:
            item_total = float(item.unit_price_rub * item.quantity)
            total_amount += item_total
            
            items_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name if item.product else "Неизвестный товар",
                "quantity": item.quantity,
                "unit_price_rub": float(item.unit_price_rub),
                "total_price_rub": item_total,
                "photo_url": item.product.get_photo_url() if item.product else "/static/images/placeholder-product.svg"
            })
        
        html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Корзина - Sirius Group V2</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50">
    <nav class="bg-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/" class="flex items-center space-x-2">
                        <i class="fas fa-store text-blue-600 text-2xl"></i>
                        <span class="text-xl font-bold text-gray-800">Sirius Group</span>
                    </a>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/" class="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                        <i class="fas fa-home mr-1"></i>Главная
                    </a>
                    <a href="/shop/" class="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                        <i class="fas fa-shopping-bag mr-1"></i>Магазин
                    </a>
                    <a href="/shop/cart" class="text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                        <i class="fas fa-shopping-cart mr-1"></i>Корзина
                    </a>
                    <a href="/admin" class="text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">
                        <i class="fas fa-cog mr-1"></i>Админ
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <main class="min-h-screen py-8">
        <div class="max-w-7xl mx-auto px-4">
            <h1 class="text-3xl font-bold text-gray-800 mb-6">
                <i class="fas fa-shopping-cart mr-2"></i>Корзина
            </h1>
            
            <div class="bg-white rounded-lg shadow-md p-6">
                <div class="space-y-4" id="cart-items">
                    <!-- Товары будут загружены через JavaScript -->
                </div>
                
                <div class="mt-8 border-t pt-6">
                    <div class="flex justify-between items-center">
                        <h2 class="text-2xl font-bold text-gray-800">Итого: <span id="total-amount">0</span> ₽</h2>
                        <button onclick="checkout()" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition duration-300">
                            <i class="fas fa-credit-card mr-2"></i>Оформить заказ
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <div id="toast-container" class="fixed top-4 right-4 z-50"></div>

    <script>
        async function loadCart() {
            try {
                const response = await fetch('/api/shop/cart/items');
                const data = await response.json();
                
                const container = document.getElementById('cart-items');
                const totalElement = document.getElementById('total-amount');
                
                if (data.items && data.items.length > 0) {
                    container.innerHTML = data.items.map(item => `
                        <div class="border rounded-lg p-4" data-product-id="${item.product_id}">
                            <div class="flex items-center space-x-4">
                                <img src="${item.photo_url}" alt="${item.product_name}" class="w-16 h-16 object-cover rounded">
                                <div class="flex-1">
                                    <h3 class="font-semibold text-gray-800">${item.product_name}</h3>
                                    <p class="text-gray-600">${item.unit_price_rub} ₽ за шт.</p>
                                </div>
                            </div>
                            <div class="mt-4 flex items-center justify-between">
                                <div class="flex items-center space-x-2">
                                    <button onclick="updateQuantity(${item.product_id}, ${item.quantity - 1})" class="bg-gray-200 text-gray-700 px-2 py-1 rounded">-</button>
                                    <span class="px-3 py-1 bg-gray-100 rounded" id="qty-${item.product_id}">${item.quantity}</span>
                                    <button onclick="updateQuantity(${item.product_id}, ${item.quantity + 1})" class="bg-gray-200 text-gray-700 px-2 py-1 rounded">+</button>
                                </div>
                                <div class="text-right">
                                    <p class="font-semibold text-lg" id="total-${item.product_id}">${item.total_price_rub} ₽</p>
                                    <button onclick="removeItem(${item.product_id})" class="text-red-500 hover:text-red-700 text-sm">
                                        <i class="fas fa-trash mr-1"></i>Удалить
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    
                    totalElement.textContent = data.total_amount;
                } else {
                    container.innerHTML = `
                        <div class="text-center py-12">
                            <i class="fas fa-shopping-cart text-6xl text-gray-300 mb-4"></i>
                            <h2 class="text-2xl font-bold text-gray-600 mb-2">Корзина пуста</h2>
                            <p class="text-gray-500 mb-6">Добавьте товары из каталога</p>
                            <a href="/shop/" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition duration-300">
                                <i class="fas fa-shopping-bag mr-2"></i>Перейти в магазин
                            </a>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading cart:', error);
            }
        }

        async function updateQuantity(productId, newQuantity) {
            if (newQuantity < 0) return;
            
            try {
                const response = await fetch(`/api/shop/cart/update/${productId}?quantity=${newQuantity}`, {
                    method: 'PUT'
                });
                
                if (response.ok) {
                    if (newQuantity === 0) {
                        const item = document.querySelector(`[data-product-id="${productId}"]`);
                        if (item) item.remove();
                        
                        const items = document.querySelectorAll('[data-product-id]');
                        if (items.length === 0) {
                            loadCart();
                        }
                    } else {
                        loadCart();
                    }
                } else {
                    showToast('Ошибка обновления корзины', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showToast('Ошибка обновления корзины', 'error');
            }
        }

        async function removeItem(productId) {
            try {
                const response = await fetch(`/api/shop/cart/remove/${productId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    loadCart();
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
        raise HTTPException(status_code=500, detail="Ошибка загрузки корзины")