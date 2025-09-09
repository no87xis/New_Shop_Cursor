# 💻 ПРИМЕРЫ КОДА И СХЕМЫ
## Дополнительная техническая документация для Sirius Group

---

## 🗄️ СХЕМЫ БАЗЫ ДАННЫХ

### **ER-диаграмма основных таблиц:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    products     │    │   shop_carts    │    │  shop_orders    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄───┤ product_id (FK) │◄───┤ product_id (FK) │
│ name            │    │ session_id      │    │ order_code      │
│ description     │    │ quantity        │    │ customer_name   │
│ sell_price_rub  │    │ created_at      │    │ customer_phone  │
│ quantity        │    │ updated_at      │    │ delivery_option │
│ availability    │    └─────────────────┘    │ payment_method  │
└─────────────────┘                          │ status          │
                                             │ qr_payload      │
                                             └─────────────────┘
```

### **Связи между таблицами:**
- `shop_carts.product_id` → `products.id` (Many-to-One)
- `shop_orders.product_id` → `products.id` (Many-to-One)
- `shop_orders.payment_method_id` → `payment_methods.id` (Many-to-One)

---

## 🔧 ПРИМЕРЫ КОДА

### **1. Сервис корзины (ShopCartService)**

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal
from ..models import ShopCart, Product, ProductPhoto
from ..schemas.shop_cart import ShopCartCreate, ShopCartSummary, ShopCartItemResponse

class ShopCartService:
    """Сервис для работы с корзиной магазина"""
    
    @staticmethod
    def add_to_cart(db: Session, cart_data: ShopCartCreate) -> ShopCart:
        """Добавляет товар в корзину"""
        
        # Проверяем существование товара
        product = db.query(Product).filter(Product.id == cart_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Проверяем наличие товара
        if product.quantity < cart_data.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Недостаточно товара на складе. Доступно: {product.quantity}"
            )
        
        # Проверяем, есть ли уже такой товар в корзине
        existing_item = db.query(ShopCart).filter(
            and_(
                ShopCart.session_id == cart_data.session_id,
                ShopCart.product_id == cart_data.product_id
            )
        ).first()
        
        if existing_item:
            # Обновляем количество
            existing_item.quantity += cart_data.quantity
            existing_item.updated_at = func.now()
            db.commit()
            db.refresh(existing_item)
            return existing_item
        else:
            # Создаём новый элемент корзины
            cart_item = ShopCart(
                session_id=cart_data.session_id,
                product_id=cart_data.product_id,
                quantity=cart_data.quantity
            )
            db.add(cart_item)
            db.commit()
            db.refresh(cart_item)
            return cart_item
    
    @staticmethod
    def get_cart_summary(db: Session, session_id: str) -> ShopCartSummary:
        """Получает сводку корзины"""
        
        cart_items = db.query(ShopCart).filter(
            ShopCart.session_id == session_id
        ).all()
        
        items = []
        total_items = 0
        total_amount = Decimal('0')
        
        for cart_item in cart_items:
            product = cart_item.product
            
            # Получаем главное фото товара
            main_photo = None
            if product.photos:
                main_photo = next((p for p in product.photos if p.is_main), product.photos[0])
            
            item_total = cart_item.quantity * product.sell_price_rub
            
            items.append(ShopCartItemResponse(
                product_id=product.id,
                product_name=product.name,
                quantity=cart_item.quantity,
                unit_price_rub=product.sell_price_rub,
                total_price=item_total,
                main_photo_url=f"/static/{main_photo.file_path}" if main_photo else None,
                available_stock=product.quantity
            ))
            
            total_items += cart_item.quantity
            total_amount += item_total
        
        return ShopCartSummary(
            items=items,
            total_items=total_items,
            total_amount=total_amount
        )
    
    @staticmethod
    def validate_cart(db: Session, session_id: str) -> List[str]:
        """Валидирует корзину и возвращает список ошибок"""
        errors = []
        
        cart_items = db.query(ShopCart).filter(
            ShopCart.session_id == session_id
        ).all()
        
        if not cart_items:
            errors.append("Корзина пуста")
            return errors
        
        for cart_item in cart_items:
            product = cart_item.product
            
            # Проверяем, что товар существует
            if not product:
                errors.append(f"Товар с ID {cart_item.product_id} не найден")
                continue
            
            # Проверяем наличие товара
            if product.quantity < cart_item.quantity:
                errors.append(
                    f"Недостаточно товара '{product.name}'. "
                    f"Доступно: {product.quantity}, запрошено: {cart_item.quantity}"
                )
            
            # Проверяем, что товар доступен для заказа
            if product.availability_status not in ['IN_STOCK', 'ON_ORDER']:
                errors.append(f"Товар '{product.name}' недоступен для заказа")
        
        return errors
```

### **2. Сервис заказов (ShopOrderService)**

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from ..models import ShopOrder, Product, Order, OrderStatus
from ..schemas.shop_order import ShopOrderCreate
from .order_code import OrderCodeService
from .qr_service import QRService

class ShopOrderService:
    """Сервис для работы с заказами магазина"""
    
    @staticmethod
    def create_orders_from_cart(db: Session, order_data: ShopOrderCreate) -> List[Order]:
        """Создаёт заказы из корзины в основной таблице orders"""
        orders = []
        
        for cart_item in order_data.cart_items:
            # Получаем информацию о товаре
            product = db.query(Product).filter(Product.id == cart_item['product_id']).first()
            if not product:
                continue
            
            # Генерируем уникальный код заказа
            order_code = OrderCodeService.generate_unique_order_code(db)
            order_code_last4 = OrderCodeService.get_last4_from_code(order_code)
            
            # Вычисляем стоимость заказа
            unit_price = product.sell_price_rub or Decimal('0')
            total_amount = unit_price * cart_item['quantity']
            
            # Определяем статус заказа (не оплачен, пока менеджер не изменит)
            status = OrderStatus.PAID_NOT_ISSUED
            
            # Вычисляем стоимость доставки
            delivery_cost = Decimal('0')
            if order_data.delivery_option and order_data.delivery_option.startswith('COURIER_') and order_data.delivery_option != 'COURIER_OTHER':
                delivery_cost = Decimal('300') * cart_item['quantity']
            
            # Создаём заказ в основной таблице orders
            order = Order(
                phone=order_data.customer_phone,
                customer_name=order_data.customer_name,
                client_city=order_data.customer_city,
                product_id=product.id,
                product_name=product.name,
                qty=cart_item['quantity'],
                unit_price_rub=unit_price,
                eur_rate=Decimal('0'),
                order_code=order_code,
                order_code_last4=order_code_last4,
                payment_method_id=order_data.payment_method_id,
                payment_instrument_id=None,
                paid_amount=None,
                paid_at=None,
                payment_method='unpaid',
                payment_note=None,
                status=status,
                issued_at=None,
                user_id='shop_user',  # Системный пользователь для заказов из магазина
                source='shop',
                qr_payload=None,
                qr_image_path=None
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            # Генерируем QR-код для заказа
            qr_payload = QRService.generate_qr_payload(order.id)
            qr_image_path = QRService.generate_qr_image(qr_payload, order.order_code)
            
            # Обновляем заказ с QR-кодом
            order.qr_payload = qr_payload
            order.qr_image_path = qr_image_path
            db.commit()
            
            orders.append(order)
        
        return orders
```

### **3. Константы доставки**

```python
from enum import Enum

class DeliveryOption(str, Enum):
    """Варианты доставки"""
    SELF_PICKUP_GROZNY = "SELF_PICKUP_GROZNY"      # Самовывоз (Склад, Грозный)
    COURIER_GROZNY = "COURIER_GROZNY"               # Доставка по Грозному
    COURIER_MAK = "COURIER_MAK"                     # Доставка в Махачкалу
    COURIER_KHAS = "COURIER_KHAS"                   # Доставка в Хасавюрт
    COURIER_OTHER = "COURIER_OTHER"                 # Другая (по согласованию)

# Стоимость доставки за единицу товара (в рублях)
DELIVERY_UNIT_PRICE_RUB = 300

# Описания вариантов доставки для пользователя
DELIVERY_OPTIONS_DISPLAY = {
    DeliveryOption.SELF_PICKUP_GROZNY: "Самовывоз (Склад, Грозный)",
    DeliveryOption.COURIER_GROZNY: "Доставка по Грозному",
    DeliveryOption.COURIER_MAK: "Доставка в Махачкалу", 
    DeliveryOption.COURIER_KHAS: "Доставка в Хасавюрт",
    DeliveryOption.COURIER_OTHER: "Другая (по согласованию)"
}

# Варианты доставки, которые требуют ввода города
DELIVERY_OPTIONS_REQUIRE_CITY = {
    DeliveryOption.COURIER_OTHER
}

# Варианты доставки с нулевой стоимостью
DELIVERY_OPTIONS_FREE = {
    DeliveryOption.SELF_PICKUP_GROZNY
}

def calculate_delivery_cost(delivery_option: DeliveryOption, quantity: int) -> int:
    """
    Рассчитывает стоимость доставки
    
    Args:
        delivery_option: Выбранный вариант доставки
        quantity: Количество единиц товара
    
    Returns:
        Стоимость доставки в рублях
    """
    if delivery_option in DELIVERY_OPTIONS_FREE:
        return 0
    
    return DELIVERY_UNIT_PRICE_RUB * quantity

def requires_city_input(delivery_option: DeliveryOption) -> bool:
    """
    Проверяет, требует ли вариант доставки ввода города
    
    Args:
        delivery_option: Выбранный вариант доставки
    
    Returns:
        True, если требуется ввод города
    """
    return delivery_option in DELIVERY_OPTIONS_REQUIRE_CITY
```

### **4. JavaScript для формы оформления заказа**

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const deliveryOptionSelect = document.getElementById('delivery_option');
    const deliveryCityOtherContainer = document.getElementById('delivery_city_other_container');
    const deliveryCityOtherInput = document.getElementById('delivery_city_other');
    const deliveryCostInfo = document.getElementById('delivery_cost_info');
    const deliveryCostText = document.getElementById('delivery_cost_text');
    const paymentMethodSelect = document.getElementById('payment_method_id');
    const courierPaymentOption = document.getElementById('courier_payment_option');
    
    // Обработка выбора способа доставки
    deliveryOptionSelect.addEventListener('change', function() {
        const selectedOption = this.value;
        const totalItems = parseInt('{{ cart.total_items }}') || 0;
        
        // Показываем/скрываем поле для ввода города
        if (selectedOption === 'COURIER_OTHER') {
            deliveryCityOtherContainer.classList.remove('hidden');
            deliveryCityOtherInput.required = true;
            deliveryCostInfo.classList.remove('hidden');
            deliveryCostText.textContent = 'Стоимость доставки будет рассчитана при оформлении заказа.';
        } else if (selectedOption === 'SELF_PICKUP_GROZNY') {
            deliveryCityOtherContainer.classList.add('hidden');
            deliveryCityOtherInput.required = false;
            deliveryCityOtherInput.value = '';
            deliveryCostInfo.classList.remove('hidden');
            deliveryCostText.textContent = 'Самовывоз - бесплатно (0 ₽)';
        } else if (selectedOption && selectedOption.startsWith('COURIER_')) {
            deliveryCityOtherContainer.classList.add('hidden');
            deliveryCityOtherInput.required = false;
            deliveryCityOtherInput.value = '';
            deliveryCostInfo.classList.remove('hidden');
            const deliveryCost = totalItems * 300;
            deliveryCostText.textContent = `Стоимость доставки: ${deliveryCost} ₽ (300 ₽ × ${totalItems} ед.)`;
        } else {
            deliveryCityOtherContainer.classList.add('hidden');
            deliveryCityOtherInput.required = false;
            deliveryCityOtherInput.value = '';
            deliveryCostInfo.classList.add('hidden');
        }
        
        // Обновляем итоговую сумму с учетом доставки
        updateTotalWithDelivery(selectedOption, totalItems);
        updateDeliverySummary(selectedOption, totalItems);
        
        // Активируем/деактивируем опцию "Наличным курьеру"
        updateCourierPaymentOption(selectedOption);
    });
    
    // Функция активации/деактивации опции "Наличным курьеру"
    function updateCourierPaymentOption(deliveryOption) {
        const cartItems = {{ cart.items|tojson|safe }};
        let hasInStockItems = false;
        let hasPreOrderItems = false;
        
        for (let item of cartItems) {
            if (item.available_stock > 0) {
                hasInStockItems = true;
            } else {
                hasPreOrderItems = true;
            }
        }
        
        // Логика активации опции "Наличным курьеру":
        // 1. Должна быть выбрана курьерская доставка (не "другой город")
        // 2. В корзине должны быть товары в наличии
        // 3. НЕ должно быть товаров под заказ/в пути
        const isCourierDelivery = deliveryOption && 
                                 deliveryOption.startsWith('COURIER_') && 
                                 deliveryOption !== 'COURIER_OTHER';
        
        const canPayToCourier = isCourierDelivery && hasInStockItems && !hasPreOrderItems;
        
        if (canPayToCourier) {
            courierPaymentOption.disabled = false;
            courierPaymentOption.classList.remove('text-gray-400');
            courierPaymentOption.classList.add('text-gray-900');
        } else {
            courierPaymentOption.disabled = true;
            courierPaymentOption.classList.add('text-gray-400');
            courierPaymentOption.classList.remove('text-gray-900');
            
            // Если была выбрана опция "Наличным курьеру", сбрасываем выбор
            if (paymentMethodSelect.value === '7') {
                paymentMethodSelect.value = '';
            }
        }
    }
    
    // Функция обновления итоговой суммы с учетом доставки
    function updateTotalWithDelivery(deliveryOption, totalItems) {
        let baseAmount = parseFloat('{{ cart.total_amount }}') || 0;
        let deliveryCost = 0;
        
        if (deliveryOption && deliveryOption.startsWith('COURIER_') && deliveryOption !== 'COURIER_OTHER') {
            deliveryCost = totalItems * 300;
        }
        
        // Учитываем проценты от способа оплаты
        const selectedPaymentMethod = paymentMethodSelect.value;
        if (selectedPaymentMethod === '1') { // СБП +1%
            baseAmount += baseAmount * 0.01;
        } else if (selectedPaymentMethod === '6') { // Б/н на р/с ИП +7%
            baseAmount += baseAmount * 0.07;
        }
        
        const totalWithDelivery = baseAmount + deliveryCost;
        
        // Обновляем отображаемую сумму
        const totalAmountElement = document.getElementById('total_amount');
        if (totalAmountElement) {
            totalAmountElement.textContent = totalWithDelivery.toFixed(2) + ' ₽';
        }
    }
    
    // Обработка выбора способа оплаты
    paymentMethodSelect.addEventListener('change', function() {
        const selectedMethod = this.value;
        let totalAmount = parseFloat('{{ cart.total_amount }}');
        
        // Убираем старые проценты если есть
        const oldPercentage = document.querySelector('.payment-percentage');
        if (oldPercentage) {
            oldPercentage.remove();
        }
        
        if (selectedMethod === '1') { // СБП +1%
            const percentage = totalAmount * 0.01;
            totalAmount += percentage;
            showPercentage(percentage, '1%');
        } else if (selectedMethod === '6') { // Б/н на р/с ИП +7%
            const percentage = totalAmount * 0.07;
            totalAmount += percentage;
            showPercentage(percentage, '7%');
        }
        
        // Обновляем отображаемую сумму
        const totalAmountElement = document.querySelector('.text-blue-600');
        if (totalAmountElement) {
            totalAmountElement.textContent = totalAmount.toFixed(2) + ' ₽';
        }
    });
    
    function showPercentage(amount, percentage) {
        const totalSection = document.querySelector('.border-t.border-gray-200.pt-4');
        if (totalSection) {
            const percentageDiv = document.createElement('div');
            percentageDiv.className = 'flex justify-between text-sm mb-2 payment-percentage';
            percentageDiv.innerHTML = `
                <span class="text-gray-600">Комиссия (${percentage}):</span>
                <span class="font-medium text-red-600">+${amount.toFixed(2)} ₽</span>
            `;
            
            // Вставляем перед итоговой суммой
            const totalRow = totalSection.querySelector('.text-lg.font-semibold');
            if (totalRow) {
                totalSection.insertBefore(percentageDiv, totalRow);
            }
        }
    }
});
```

### **5. HTML шаблон корзины**

```html
{% extends "shop/base.html" %}

{% block title %}Корзина{% endblock %}

{% block content %}
<div class="px-4 sm:px-6 lg:px-8 py-6">
    <!-- Заголовок -->
    <div class="mb-6">
        <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Корзина</h1>
        <p class="text-gray-600 text-sm sm:text-base">Управляйте товарами в корзине</p>
    </div>

    {% if cart.items %}
    <!-- Товары в корзине -->
    <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <div class="px-4 sm:px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">Товары в корзине</h2>
        </div>
        
        <div class="divide-y divide-gray-200">
            {% for item in cart.items %}
            <div class="p-4 sm:p-6">
                <div class="flex items-center space-x-4">
                    <!-- Фото товара -->
                    <div class="flex-shrink-0">
                        {% if item.main_photo_url %}
                        <img src="{{ item.main_photo_url }}" 
                             alt="{{ item.product_name }}"
                             class="w-16 h-16 object-cover object-center rounded-lg">
                        {% else %}
                        <div class="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                            <i class="fas fa-image text-gray-400 text-xl"></i>
                        </div>
                        {% endif %}
                    </div>
                    
                    <!-- Информация о товаре -->
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-medium text-gray-900 truncate">
                            {{ item.product_name }}
                        </h3>
                        <p class="text-sm text-gray-500">
                            {{ "%.2f"|format(item.unit_price_rub) }} ₽ за единицу
                        </p>
                        <p class="text-sm text-gray-500">
                            В наличии: {{ item.available_stock }} шт.
                        </p>
                    </div>
                    
                    <!-- Управление количеством -->
                    <div class="flex items-center space-x-2">
                        <button onclick="updateQuantity({{ item.product_id }}, {{ item.quantity - 1 }})"
                                class="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50">
                            <i class="fas fa-minus text-sm text-gray-600"></i>
                        </button>
                        
                        <span class="w-12 text-center font-medium">{{ item.quantity }}</span>
                        
                        <button onclick="updateQuantity({{ item.product_id }}, {{ item.quantity + 1 }})"
                                class="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50">
                            <i class="fas fa-plus text-sm text-gray-600"></i>
                        </button>
                    </div>
                    
                    <!-- Стоимость -->
                    <div class="text-right">
                        <p class="text-lg font-semibold text-gray-900">
                            {{ "%.2f"|format(item.total_price) }} ₽
                        </p>
                    </div>
                    
                    <!-- Кнопка удаления -->
                    <div class="flex-shrink-0">
                        <button onclick="removeFromCart({{ item.product_id }})"
                                class="text-red-600 hover:text-red-800 p-2">
                            <i class="fas fa-trash text-lg"></i>
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <!-- Итого -->
        <div class="px-4 sm:px-6 py-4 bg-gray-50 border-t border-gray-200">
            <div class="flex justify-between items-center">
                <div>
                    <p class="text-sm text-gray-600">Товаров в корзине: {{ cart.total_items }}</p>
                    <p class="text-lg font-semibold text-gray-900">
                        Итого: {{ "%.2f"|format(cart.total_amount) }} ₽
                    </p>
                </div>
                
                <a href="/shop/checkout"
                   class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors duration-200">
                    Оформить заказ
                </a>
            </div>
        </div>
    </div>
    
    {% else %}
    <!-- Пустая корзина -->
    <div class="text-center py-12">
        <i class="fas fa-shopping-cart text-gray-300 text-6xl mb-4"></i>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Корзина пуста</h3>
        <p class="text-gray-500 mb-6">Добавьте товары в корзину, чтобы оформить заказ</p>
        <a href="/shop" 
           class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors duration-200">
            Перейти к каталогу
        </a>
    </div>
    {% endif %}
</div>

<script>
// Функции для управления корзиной
function updateQuantity(productId, newQuantity) {
    if (newQuantity < 1) {
        removeFromCart(productId);
        return;
    }
    
    fetch(`/api/shop/cart/update/${productId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quantity: newQuantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Ошибка: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при обновлении корзины');
    });
}

function removeFromCart(productId) {
    if (confirm('Удалить товар из корзины?')) {
        fetch(`/api/shop/cart/remove/${productId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Ошибка: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Произошла ошибка при удалении товара');
        });
    }
}
</script>
{% endblock %}
```

---

## 📊 СХЕМЫ ПРОЦЕССОВ

### **1. Процесс добавления товара в корзину:**
```
Пользователь → Выбирает товар → Нажимает "Добавить в корзину"
    ↓
Проверка наличия товара на складе
    ↓
Товар есть? → НЕТ → Показать ошибку
    ↓ ДА
Товар уже в корзине? → ДА → Увеличить количество
    ↓ НЕТ
Создать новую запись в корзине
    ↓
Обновить счетчик корзины в UI
    ↓
Показать уведомление об успехе
```

### **2. Процесс оформления заказа:**
```
Пользователь → Заполняет форму → Нажимает "Оформить заказ"
    ↓
Валидация формы
    ↓
Форма корректна? → НЕТ → Показать ошибки
    ↓ ДА
Валидация корзины
    ↓
Корзина валидна? → НЕТ → Показать ошибки
    ↓ ДА
Создание заказов для каждого товара
    ↓
Генерация кодов заказов
    ↓
Расчет стоимости доставки
    ↓
Генерация QR-кодов
    ↓
Резервирование товаров (48 часов)
    ↓
Очистка корзины
    ↓
Перенаправление на страницу успеха
```

### **3. Процесс расчета стоимости:**
```
Стоимость товаров
    ↓
+ Стоимость доставки (300₽ × количество)
    ↓
+ Проценты за способ оплаты (СБП +1%, Б/н +7%)
    ↓
= Итоговая сумма к оплате
```

---

## 🧪 ТЕСТОВЫЕ СЦЕНАРИИ

### **1. Тест добавления товара в корзину:**
```python
def test_add_to_cart():
    # Подготовка
    product = create_test_product(quantity=10)
    session_id = "test_session_123"
    
    # Действие
    response = client.post("/api/shop/cart/add", json={
        "product_id": product.id,
        "quantity": 2
    })
    
    # Проверка
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    
    # Проверка в базе данных
    cart_item = db.query(ShopCart).filter(
        ShopCart.session_id == session_id,
        ShopCart.product_id == product.id
    ).first()
    assert cart_item.quantity == 2
```

### **2. Тест оформления заказа:**
```python
def test_create_order():
    # Подготовка
    product = create_test_product(quantity=10)
    add_to_cart(product.id, 2)
    
    # Действие
    response = client.post("/shop/checkout", data={
        "customer_name": "Иван Иванов",
        "customer_phone": "+7 (999) 123-45-67",
        "customer_city": "Грозный",
        "delivery_option": "SELF_PICKUP_GROZNY",
        "payment_method_id": "2"
    })
    
    # Проверка
    assert response.status_code == 303  # Redirect
    assert "/shop/order-success" in response.headers["location"]
    
    # Проверка создания заказа
    order = db.query(Order).filter(
        Order.customer_name == "Иван Иванов"
    ).first()
    assert order is not None
    assert order.qty == 2
```

### **3. Тест расчета стоимости доставки:**
```python
def test_delivery_cost_calculation():
    # Самовывоз - бесплатно
    cost = calculate_delivery_cost("SELF_PICKUP_GROZNY", 5)
    assert cost == 0
    
    # Курьерская доставка - 300₽ за единицу
    cost = calculate_delivery_cost("COURIER_GROZNY", 3)
    assert cost == 900  # 300 * 3
    
    # Другая доставка - 300₽ за единицу
    cost = calculate_delivery_cost("COURIER_OTHER", 2)
    assert cost == 600  # 300 * 2
```

---

## 🔧 КОНФИГУРАЦИЯ

### **Настройки базы данных:**
```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./sirius.db"
    secret_key: str = "your-secret-key-32-characters-long"
    debug: bool = True
    
    # Настройки доставки
    delivery_unit_price: int = 300
    reservation_hours: int = 48
    
    # Настройки оплаты
    sbp_percentage: float = 0.01  # 1%
    bank_transfer_percentage: float = 0.07  # 7%
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### **Настройки CORS:**
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📱 МОБИЛЬНАЯ ОПТИМИЗАЦИЯ

### **CSS для мобильных устройств:**
```css
/* Мобильная корзина */
@media (max-width: 640px) {
    .cart-item {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .cart-item-photo {
        width: 100%;
        height: 200px;
        object-fit: cover;
    }
    
    .cart-item-controls {
        width: 100%;
        justify-content: space-between;
    }
    
    .quantity-controls {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
}

/* Мобильная форма заказа */
@media (max-width: 640px) {
    .checkout-form {
        padding: 1rem;
    }
    
    .form-group {
        margin-bottom: 1.5rem;
    }
    
    .form-input {
        width: 100%;
        padding: 0.75rem;
        font-size: 16px; /* Предотвращает зум на iOS */
    }
}
```

### **JavaScript для мобильных устройств:**
```javascript
// Определение мобильного устройства
function isMobile() {
    return window.innerWidth <= 768;
}

// Адаптивное поведение
if (isMobile()) {
    // Увеличиваем размер кнопок для touch-устройств
    document.querySelectorAll('button').forEach(button => {
        button.style.minHeight = '44px';
        button.style.minWidth = '44px';
    });
    
    // Оптимизируем формы для мобильных
    document.querySelectorAll('input[type="tel"]').forEach(input => {
        input.setAttribute('inputmode', 'tel');
    });
}
```

---

**Документ создан:** 2025-01-27  
**Версия:** 1.0  
**Статус:** Дополнительная техническая документация

Этот документ содержит практические примеры кода, схемы процессов и тестовые сценарии для реализации системы корзины и оформления заказов Sirius Group.
