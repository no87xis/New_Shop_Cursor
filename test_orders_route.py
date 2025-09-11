@router.get("/admin/test-orders", response_class=HTMLResponse)
async def test_orders_page(request: Request):
    """
    Страница управления тестовыми заказами
    """
    try:
        return templates.TemplateResponse("admin/test_orders.html", {
            "request": request
        })
    except Exception as e:
        logger.error(f"Error loading test orders page: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Ошибка загрузки страницы тестовых заказов: {e}"
        })