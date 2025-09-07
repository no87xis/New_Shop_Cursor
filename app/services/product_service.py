from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from typing import List, Optional
from datetime import date

class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, product_data: ProductCreate) -> Product:
        product = Product(**product_data.dict())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_all(self) -> List[Product]:
        return self.db.query(Product).all()
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def update(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if product:
            for key, value in product_data.dict().items():
                if value is not None:
                    setattr(product, key, value)
            self.db.commit()
            self.db.refresh(product)
        return product
    
    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if product:
            self.db.delete(product)
            self.db.commit()
            return True
        return False
    
    def update_quantity(self, product_id: int, new_quantity: int) -> Optional[Product]:
        product = self.get_by_id(product_id)
        if product:
            product.quantity = new_quantity
            
            # Обновляем статус в зависимости от количества
            if new_quantity <= 0:
                product.availability_status = "ON_ORDER"
            elif new_quantity <= product.min_stock:
                if product.availability_status == "IN_STOCK":
                    product.availability_status = "ON_ORDER"
            else:
                if product.availability_status == "ON_ORDER":
                    product.availability_status = "IN_STOCK"
            
            self.db.commit()
            self.db.refresh(product)
        return product
    
    def get_statistics(self) -> dict:
        products = self.get_all()
        total = len(products)
        in_stock = len([p for p in products if p.availability_status == "IN_STOCK"])
        in_transit = len([p for p in products if p.availability_status == "IN_TRANSIT"])
        on_order = len([p for p in products if p.availability_status == "ON_ORDER"])
        low_stock = len([p for p in products if p.quantity <= p.min_stock and p.quantity > 0])
        
        return {
            "total": total,
            "in_stock": in_stock,
            "in_transit": in_transit,
            "on_order": on_order,
            "low_stock": low_stock
        }