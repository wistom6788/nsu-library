"""
Student lookup page — 学生查询
"""
import json
from pathlib import Path
from fastapi import APIRouter, Request, Query
from app.data.loader import load_access, load_borrows, load_students

router = APIRouter()


@router.get("/student")
async def student_page(request: Request):
    """Render the student lookup page."""
    return request.app.state.templates.TemplateResponse("student.html", {
        "request": request,
        "active_page": "student",
    })


@router.get("/api/student/search")
async def student_search(q: str = Query(..., min_length=1, description="Search query")):
    """Search students by name or ID. Returns top 20 matches."""
    df_students = load_students()
    q_lower = q.strip().lower()

    # Search by name or student ID
    mask_name = df_students["姓名"].str.lower().str.contains(q_lower, na=False)
    mask_id = df_students["学号"].astype(str).str.contains(q, na=False)
    matches = df_students[mask_name | mask_id].head(20)

    results = []
    for _, row in matches.iterrows():
        results.append({
            "student_id": str(row["学号"]),
            "name": row["姓名"],
            "college": row["学院"],
            "major": row["专业"],
            "class_name": row["行政班号"],
        })
    return {"results": results}


@router.get("/api/student/{student_id}")
async def student_detail(student_id: str):
    """Return detailed data for a specific student."""
    df_students = load_students()
    df_access = load_access()
    df_borrows = load_borrows()

    # Student info
    stu = df_students[df_students["学号"].astype(str) == student_id]
    if stu.empty:
        return {"error": "未找到该学生"}
    stu = stu.iloc[0]
    student_info = {
        "student_id": student_id,
        "name": stu["姓名"],
        "college": stu["学院"],
        "major": stu["专业"],
        "class_name": stu["行政班号"],
    }

    # Access stats
    stu_access = df_access[df_access["学号/工号"].astype(str) == student_id]
    access_stats = {}
    if not stu_access.empty:
        access_stats = {
            "total_visits": int(stu_access["到馆次数"].sum()),
            "total_duration_h": round(float(stu_access["在馆时长(h)"].sum()), 2),
            "avg_duration_h": round(float(stu_access["在馆时长(h)"].mean()), 2),
            "first_visit": str(stu_access.index.min().date()),
            "last_visit": str(stu_access.index.max().date()),
        }
        # Monthly visit trend
        monthly = stu_access["到馆次数"].resample("ME").sum()
        access_stats["monthly_visits"] = {
            "x": [t.strftime("%Y-%m") for t in monthly.index],
            "y": [int(v) for v in monthly.values],
        }
        # Hourly pattern
        hourly = stu_access.groupby("hour")["到馆次数"].sum()
        access_stats["hourly_visits"] = {
            "x": [int(h) for h in hourly.index],
            "y": [int(v) for v in hourly.values],
        }
        # Weekday pattern
        from app.data.precompute import WEEKDAY_LABELS
        weekday = stu_access.groupby("weekday")["到馆次数"].sum()
        access_stats["weekday_visits"] = {
            "x": WEEKDAY_LABELS,
            "y": [int(weekday.get(i, 0)) for i in range(7)],
        }

    # Borrow stats
    stu_borrows = df_borrows[df_borrows["读者证号"].astype(str) == student_id]
    borrow_stats = {}
    if not stu_borrows.empty:
        borrow_stats = {
            "total_borrows": len(stu_borrows),
            "avg_duration_d": round(float(stu_borrows["借阅时长"].mean()), 2),
        }
        # Monthly borrow trend
        monthly_b = stu_borrows.groupby(stu_borrows["操作日期"].dt.to_period("M")).size()
        borrow_stats["monthly_borrows"] = {
            "x": [str(p) for p in monthly_b.index],
            "y": [int(v) for v in monthly_b.values],
        }

    return {
        "info": student_info,
        "access": access_stats,
        "borrow": borrow_stats,
    }
