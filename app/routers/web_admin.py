from fastapi import APIRouter, Depends, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.product_service import ProductService
from app.schemas.product import ProductCreate, ProductUpdate
import os
import uuid
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    stats = product_service.get_statistics()
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats
    })

@router.get("/admin/products", response_class=HTMLResponse)
async def admin_products(request: Request, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    products = product_service.get_all()
    stats = product_service.get_statistics()
    return templates.TemplateResponse("admin/products.html", {
        "request": request,
        "products": products,
        "stats": stats
    })

@router.post("/admin/products")
async def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(0),
    min_stock: int = Form(0),
    buy_price_eur: float = Form(None),
    sell_price_rub: float = Form(...),
    supplier_name: str = Form(""),
    availability_status: str = Form("IN_STOCK"),
    expected_date: str = Form(None),
    product_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Проверка доступа (упрощенная)
    if not request.session.get("admin_logged_in"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    product_service = ProductService(db)
    
    # Проверка на существующий товар
    existing_products = product_service.get_all()
    for product in existing_products:
        if product.name.lower() == name.lower():
            raise HTTPException(status_code=400, detail="Товар с таким названием уже существует")
    
    # Обработка фото
    photo_path = None
    if product_photo and product_photo.filename:
        upload_dir = "uploads/products"
        os.makedirs(upload_dir, exist_ok=True)
        file_extension = os.path.splitext(product_photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        photo_path = os.path.join(upload_dir, unique_filename)
        
        with open(photo_path, "wb") as buffer:
            content = await product_photo.read()
            buffer.write(content)
    
    # Обработка даты
    expected_date_obj = None
    if expected_date:
        try:
            expected_date_obj = datetime.strptime(expected_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    product_data = ProductCreate(
        name=name,
        description=description,
        quantity=quantity,
        min_stock=min_stock,
        buy_price_eur=buy_price_eur,
        sell_price_rub=sell_price_rub,
        supplier_name=supplier_name,
        availability_status=availability_status,
        expected_date=expected_date_obj,
        photo_path=photo_path
    )
    
    product = product_service.create(product_data)
    return RedirectResponse(url="/admin/products", status_code=302)

@router.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(request: Request, product_id: int, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return templates.TemplateResponse("admin/product_edit.html", {
        "request": request,
        "product": product
    })

@router.post("/admin/products/{product_id}/update")
async def update_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    quantity: int = Form(0),
    min_stock: int = Form(0),
    buy_price_eur: float = Form(None),
    sell_price_rub: float = Form(...),
    supplier_name: str = Form(""),
    availability_status: str = Form("IN_STOCK"),
    expected_date: str = Form(None),
    product_photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Обработка фото
    photo_path = product.photo_path
    if product_photo and product_photo.filename:
        upload_dir = "uploads/products"
        os.makedirs(upload_dir, exist_ok=True)
        file_extension = os.path.splitext(product_photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        photo_path = os.path.join(upload_dir, unique_filename)
        
        with open(photo_path, "wb") as buffer:
            content = await product_photo.read()
            buffer.write(content)
    
    # Обработка даты
    expected_date_obj = None
    if expected_date:
        try:
            expected_date_obj = datetime.strptime(expected_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    product_data = ProductUpdate(
        name=name,
        description=description,
        quantity=quantity,
        min_stock=min_stock,
        buy_price_eur=buy_price_eur,
        sell_price_rub=sell_price_rub,
        supplier_name=supplier_name,
        availability_status=availability_status,
        expected_date=expected_date_obj,
        photo_path=photo_path
    )
    
    product_service.update(product_id, product_data)
    return RedirectResponse(url="/admin/products", status_code=302)

@router.post("/admin/products/{product_id}/delete")
async def delete_product(request: Request, product_id: int, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    success = product_service.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return RedirectResponse(url="/admin/products", status_code=302)

@router.post("/admin/products/{product_id}/update-quantity")
async def update_product_quantity(
    request: Request,
    product_id: int,
    new_quantity: int = Form(...),
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    product = product_service.update_quantity(product_id, new_quantity)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return RedirectResponse(url="/admin/products", status_code=302)

@router.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("admin/orders.html", {
        "request": request,
        "orders": []
    })

@router.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    stats = product_service.get_statistics()
    return templates.TemplateResponse("admin/analytics.html", {
        "request": request,
        "stats": stats
    })