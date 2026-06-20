"""
Overview page — KPI cards + summary charts.
"""
from fastapi import APIRouter, Request

from app.services.cache import load_cached

router = APIRouter()


@router.get("/")
async def index(request: Request):
    """Render the overview dashboard page."""
    return request.app.state.templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "overview",
    })


@router.get("/api/overview")
async def api_overview():
    """Return overview KPI data."""
    return load_cached("overview")


@router.get("/api/overview/charts")
async def api_overview_charts():
    """Return summary charts for overview page."""
    return {
        "monthly_visits": load_cached("access_monthly_visits"),
        "college_visits": load_cached("access_college_visits"),
        "borrow_monthly": load_cached("borrow_monthly"),
    }
