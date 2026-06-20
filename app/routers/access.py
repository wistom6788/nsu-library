"""
Access analysis page — 到馆数据分析
"""
from fastapi import APIRouter, Request

from app.services.cache import load_cached

router = APIRouter()


@router.get("/access")
async def access_page(request: Request):
    """Render the access analysis page."""
    return request.app.state.templates.TemplateResponse("access.html", {
        "request": request,
        "active_page": "access",
    })


@router.get("/api/access/overview")
async def api_access_overview():
    """Return overview stats for access page."""
    return load_cached("overview")


# Time analysis (1.1.x)
@router.get("/api/access/monthly-visits")
async def api_access_monthly_visits():
    return load_cached("access_monthly_visits")


@router.get("/api/access/daily-visits")
async def api_access_daily_visits():
    return load_cached("access_daily_visits")


@router.get("/api/access/weekday-visits")
async def api_access_weekday_visits():
    return load_cached("access_weekday_visits")


@router.get("/api/access/hourly-visits")
async def api_access_hourly_visits():
    return load_cached("access_hourly_visits")


@router.get("/api/access/monthly-duration")
async def api_access_monthly_duration():
    return load_cached("access_monthly_duration")


@router.get("/api/access/monthly-avg-duration")
async def api_access_monthly_avg_duration():
    return load_cached("access_monthly_avg_duration")


@router.get("/api/access/daily-duration")
async def api_access_daily_duration():
    return load_cached("access_daily_duration")


@router.get("/api/access/daily-avg-duration")
async def api_access_daily_avg_duration():
    return load_cached("access_daily_avg_duration")


@router.get("/api/access/weekday-duration")
async def api_access_weekday_duration():
    return load_cached("access_weekday_duration")


@router.get("/api/access/weekday-avg-duration")
async def api_access_weekday_avg_duration():
    return load_cached("access_weekday_avg_duration")


# College analysis (1.2.x)
@router.get("/api/access/college-visits")
async def api_access_college_visits():
    return load_cached("access_college_visits")


@router.get("/api/access/college-students")
async def api_access_college_students():
    return load_cached("access_college_students")


@router.get("/api/access/college-duration")
async def api_access_college_duration():
    return load_cached("access_college_duration")


@router.get("/api/access/college-avg-duration")
async def api_access_college_avg_duration():
    return load_cached("access_college_avg_duration")


@router.get("/api/access/college-monthly-visits")
async def api_access_college_monthly_visits():
    return load_cached("access_college_monthly_visits")


@router.get("/api/access/college-monthly-duration")
async def api_access_college_monthly_duration():
    return load_cached("access_college_monthly_duration")


# Major & Class analysis (1.3.x)
@router.get("/api/access/major-visits")
async def api_access_major_visits():
    return load_cached("access_major_visits")


@router.get("/api/access/major-duration")
async def api_access_major_duration():
    return load_cached("access_major_duration")


@router.get("/api/access/class-visits")
async def api_access_class_visits():
    return load_cached("access_class_visits")


@router.get("/api/access/class-duration")
async def api_access_class_duration():
    return load_cached("access_class_duration")


# Student analysis (1.4.x)
@router.get("/api/access/student-top-visits")
async def api_access_student_top_visits():
    return load_cached("access_student_top_visits")


@router.get("/api/access/student-top-duration")
async def api_access_student_top_duration():
    return load_cached("access_student_top_duration")


@router.get("/api/access/college-visit-boxplot")
async def api_access_college_visit_boxplot():
    return load_cached("access_college_visit_boxplot")


@router.get("/api/access/college-duration-boxplot")
async def api_access_college_duration_boxplot():
    return load_cached("access_college_duration_boxplot")


@router.get("/api/access/scatter")
async def api_access_scatter():
    return load_cached("access_scatter")
