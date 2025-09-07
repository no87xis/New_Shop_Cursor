from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.product_service import ProductService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def shop_home(request: Request, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    products = product_service.get_all()
    return templates.TemplateResponse("shop/catalog.html", {
        "request": request,
        "products": products
    })

@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    product = product_service.get_by_id(product_id)
    if not product:
        return templates.TemplateResponse("shop/404.html", {
            "request": request,
            "message": "Товар не найден"
        })
    
    return templates.TemplateResponse("shop/product_detail.html", {
        "request": request,
        "product": product
    })