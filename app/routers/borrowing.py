"""
Borrowing analysis page — 借还数据分析
"""
from fastapi import APIRouter, Request

from app.services.cache import load_cached

router = APIRouter()


@router.get("/borrowing")
async def borrowing_page(request: Request):
    """Render the borrowing analysis page."""
    return request.app.state.templates.TemplateResponse("borrowing.html", {
        "request": request,
        "active_page": "borrowing",
    })


@router.get("/api/borrowing/monthly")
async def api_borrow_monthly():
    return load_cached("borrow_monthly")


@router.get("/api/borrowing/hourly")
async def api_borrow_hourly():
    return load_cached("borrow_hourly")


@router.get("/api/borrowing/college")
async def api_borrow_college():
    return load_cached("borrow_college")


@router.get("/api/borrowing/college-per-capita")
async def api_borrow_college_per_capita():
    return load_cached("borrow_college_per_capita")


@router.get("/api/borrowing/major")
async def api_borrow_major():
    return load_cached("borrow_major")


@router.get("/api/borrowing/classifications")
async def api_borrow_classifications():
    return load_cached("borrow_classifications")


@router.get("/api/borrowing/top-books")
async def api_borrow_top_books():
    return load_cached("borrow_top_books")


@router.get("/api/borrowing/duration")
async def api_borrow_duration():
    return load_cached("borrow_duration")


@router.get("/api/borrowing/college-duration")
async def api_borrow_college_duration():
    return load_cached("borrow_college_duration")
