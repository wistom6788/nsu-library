"""
Pre-compute all chart aggregations and save as JSON files in cache/.
Run once: python -m app.data.precompute
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import CACHE_DIR
from app.data.loader import load_access, load_borrows, load_students, load_classifications


def save_json(name: str, data: dict):
    """Save a dict as JSON in the cache directory."""
    path = CACHE_DIR / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {name}.json")


def month_label(ts) -> str:
    """Format a Timestamp as 'YYYY-MM'."""
    return ts.strftime("%Y-%m")


WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


# =========================================================================
# OVERVIEW KPIs
# =========================================================================

def compute_overview(df_access: pd.DataFrame, df_borrows: pd.DataFrame):
    """Compute overview KPI cards."""
    total_visits = int(df_access["到馆次数"].sum())
    total_borrows = len(df_borrows)
    avg_duration_h = round(float(df_access["在馆时长(h)"].mean()), 2)

    data = {
        "total_visits": total_visits,
        "total_borrows": total_borrows,
        "avg_duration_h": avg_duration_h,
        "data_start": "2023-10-31",
        "data_end": "2024-06-30",
    }
    save_json("overview", data)


# =========================================================================
# ACCESS — TIME ANALYSIS (1.1.x)
# =========================================================================

def compute_access_monthly_visits(df: pd.DataFrame):
    """1.1.1 每月到馆人次柱形图"""
    monthly = df["到馆次数"].resample("ME").sum()
    data = {
        "x": [month_label(t) for t in monthly.index],
        "y": [int(v) for v in monthly.values],
        "title": "每月到馆人次",
        "x_label": "月份",
        "y_label": "到馆人次",
    }
    save_json("access_monthly_visits", data)


def compute_access_daily_visits(df: pd.DataFrame):
    """1.1.2 每日到馆人数统计（按真实日期聚合，避免不同月份同一天被合并）"""
    daily = df["到馆次数"].resample("D").sum()
    data = {
        "x": [t.strftime("%Y-%m-%d") for t in daily.index],
        "y": [int(v) for v in daily.values],
        "title": "每日到馆人数统计",
        "x_label": "日期",
        "y_label": "到馆人次",
    }
    save_json("access_daily_visits", data)


def compute_access_weekday_visits(df: pd.DataFrame):
    """1.1.3 每周到馆人数统计"""
    weekday = df.groupby("weekday")["到馆次数"].sum()
    data = {
        "x": WEEKDAY_LABELS,
        "y": [int(weekday.get(i, 0)) for i in range(7)],
        "title": "每周各天到馆人数统计",
        "x_label": "星期",
        "y_label": "到馆人次",
    }
    save_json("access_weekday_visits", data)


def compute_access_hourly_visits(df: pd.DataFrame):
    """1.1.4 每小时到馆人数折线图"""
    hourly = df.groupby("hour")["到馆次数"].sum()
    avg_val = round(float(hourly.mean()), 2)
    data = {
        "x": [int(h) for h in hourly.index],
        "y": [int(v) for v in hourly.values],
        "avg": avg_val,
        "title": "每小时到馆人数",
        "x_label": "小时",
        "y_label": "到馆人次",
    }
    save_json("access_hourly_visits", data)


def compute_access_monthly_duration(df: pd.DataFrame):
    """1.1.5 每月在馆时长柱形图"""
    monthly = df["在馆时长(h)"].resample("ME").sum()
    avg_val = round(float(monthly.mean()), 2)
    data = {
        "x": [month_label(t) for t in monthly.index],
        "y": [round(float(v), 2) for v in monthly.values],
        "avg": avg_val,
        "title": "每月在馆总时长（小时）",
        "x_label": "月份",
        "y_label": "时长（小时）",
    }
    save_json("access_monthly_duration", data)


def compute_access_monthly_avg_duration(df: pd.DataFrame):
    """1.1.5-2 每月平均在馆时长柱形图"""
    monthly_dur = df["在馆时长(h)"].resample("ME").sum()
    monthly_cnt = df["到馆次数"].resample("ME").sum()
    avg_dur = (monthly_dur / monthly_cnt).round(2)
    data = {
        "x": [month_label(t) for t in avg_dur.index],
        "y": [round(float(v), 2) for v in avg_dur.values],
        "title": "每月平均在馆时长（小时）",
        "x_label": "月份",
        "y_label": "平均时长（小时）",
    }
    save_json("access_monthly_avg_duration", data)


def compute_access_daily_duration(df: pd.DataFrame):
    """1.1.6-1 每日在馆时长统计（按真实日期聚合，避免不同月份同一天被合并）"""
    daily = df["在馆时长(h)"].resample("D").sum()
    data = {
        "x": [t.strftime("%Y-%m-%d") for t in daily.index],
        "y": [round(float(v), 2) for v in daily.values],
        "title": "每日在馆总时长（小时）",
        "x_label": "日期",
        "y_label": "时长（小时）",
    }
    save_json("access_daily_duration", data)


def compute_access_daily_avg_duration(df: pd.DataFrame):
    """1.1.6-2 每日平均在馆时长柱形图"""
    daily_dur = df.groupby("day_of_month")["在馆时长(h)"].sum()
    daily_cnt = df.groupby("day_of_month")["到馆次数"].sum()
    avg_dur = (daily_dur / daily_cnt).round(2)
    data = {
        "x": [int(d) for d in avg_dur.index],
        "y": [round(float(v), 2) for v in avg_dur.values],
        "title": "每日平均在馆时长（小时）",
        "x_label": "日",
        "y_label": "平均时长（小时）",
    }
    save_json("access_daily_avg_duration", data)


def compute_access_weekday_duration(df: pd.DataFrame):
    """1.1.7-1 每周各天在馆时长统计"""
    weekday = df.groupby("weekday")["在馆时长(h)"].sum()
    data = {
        "x": WEEKDAY_LABELS,
        "y": [round(float(weekday.get(i, 0)), 2) for i in range(7)],
        "title": "每周各天在馆总时长（小时）",
        "x_label": "星期",
        "y_label": "时长（小时）",
    }
    save_json("access_weekday_duration", data)


def compute_access_weekday_avg_duration(df: pd.DataFrame):
    """1.1.7-2 每周各天在馆平均时长统计"""
    w_dur = df.groupby("weekday")["在馆时长(h)"].sum()
    w_cnt = df.groupby("weekday")["到馆次数"].sum()
    avg_dur = (w_dur / w_cnt).round(2)
    data = {
        "x": WEEKDAY_LABELS,
        "y": [round(float(avg_dur.get(i, 0)), 2) for i in range(7)],
        "title": "每周各天平均在馆时长（小时）",
        "x_label": "星期",
        "y_label": "平均时长（小时）",
    }
    save_json("access_weekday_avg_duration", data)


# =========================================================================
# ACCESS — COLLEGE ANALYSIS (1.2.x)
# =========================================================================

def compute_access_college_visits(df: pd.DataFrame):
    """1.2.1 各学院到馆人次排名"""
    college = df.groupby("一级部门")["到馆次数"].sum().sort_values(ascending=False)
    data = {
        "x": list(college.index),
        "y": [int(v) for v in college.values],
        "title": "各学院到馆人次排名",
        "x_label": "学院",
        "y_label": "到馆人次",
    }
    save_json("access_college_visits", data)


def compute_access_college_students(df: pd.DataFrame):
    """1.2.1-2 各学院到馆人数排名"""
    college = df.groupby("一级部门")["学号/工号"].nunique().sort_values(ascending=False)
    data = {
        "x": list(college.index),
        "y": [int(v) for v in college.values],
        "title": "各学院到馆学生人数排名",
        "x_label": "学院",
        "y_label": "学生人数",
    }
    save_json("access_college_students", data)


def compute_access_college_duration(df: pd.DataFrame):
    """1.2.2-1 各学院在馆总时长排名"""
    college = df.groupby("一级部门")["在馆时长(h)"].sum().sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in college.values],
        "y": list(college.index),
        "title": "各学院在馆总时长排名（小时）",
        "x_label": "时长（小时）",
        "y_label": "学院",
    }
    save_json("access_college_duration", data)


def compute_access_college_avg_duration(df: pd.DataFrame):
    """1.2.2-2 各学院生均在馆总时长排名"""
    total_dur = df.groupby("一级部门")["在馆时长(h)"].sum()
    student_cnt = df.groupby("一级部门")["学号/工号"].nunique()
    avg_dur = (total_dur / student_cnt).sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in avg_dur.values],
        "y": list(avg_dur.index),
        "title": "各学院生均在馆时长排名（小时）",
        "x_label": "生均时长（小时）",
        "y_label": "学院",
    }
    save_json("access_college_avg_duration", data)


def compute_access_college_monthly_visits(df: pd.DataFrame):
    """1.2.3 各学院每月到馆人数折线图"""
    grouped = df.groupby("一级部门")["到馆次数"].resample("ME").sum()
    colleges = sorted(df["一级部门"].unique())
    months = sorted(grouped.index.get_level_values(1).unique())
    series = {}
    for college in colleges:
        vals = []
        for m in months:
            try:
                vals.append(int(grouped.loc[(college, m)]))
            except KeyError:
                vals.append(0)
        series[college] = vals
    data = {
        "x": [month_label(m) for m in months],
        "series": series,
        "title": "各学院每月到馆人次",
        "x_label": "月份",
        "y_label": "到馆人次",
    }
    save_json("access_college_monthly_visits", data)


def compute_access_college_monthly_duration(df: pd.DataFrame):
    """1.2.4 各学院每月在馆时长折线图"""
    grouped = df.groupby("一级部门")["在馆时长(h)"].resample("ME").sum()
    colleges = sorted(df["一级部门"].unique())
    months = sorted(grouped.index.get_level_values(1).unique())
    series = {}
    for college in colleges:
        vals = []
        for m in months:
            try:
                vals.append(round(float(grouped.loc[(college, m)]), 2))
            except KeyError:
                vals.append(0)
        series[college] = vals
    data = {
        "x": [month_label(m) for m in months],
        "series": series,
        "title": "各学院每月在馆时长（小时）",
        "x_label": "月份",
        "y_label": "时长（小时）",
    }
    save_json("access_college_monthly_duration", data)


# =========================================================================
# ACCESS — MAJOR & CLASS ANALYSIS (1.3.x)
# =========================================================================

def compute_access_major_visits(df: pd.DataFrame):
    """1.3.1 各专业到馆次数排名 TOP 20"""
    major = df.groupby("二级部门")["到馆次数"].sum().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [int(v) for v in major.values],
        "y": list(major.index),
        "title": "各专业到馆次数排名 TOP 20",
        "x_label": "到馆次数",
        "y_label": "专业",
    }
    save_json("access_major_visits", data)


def compute_access_major_duration(df: pd.DataFrame):
    """1.3.2 各专业在馆时长排名 TOP 20"""
    major = df.groupby("二级部门")["在馆时长(h)"].sum().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in major.values],
        "y": list(major.index),
        "title": "各专业在馆时长排名 TOP 20（小时）",
        "x_label": "时长（小时）",
        "y_label": "专业",
    }
    save_json("access_major_duration", data)


def compute_access_class_visits(df: pd.DataFrame):
    """1.3.3 各班级到馆次数排名 TOP 20"""
    cls = df.groupby("三级部门")["到馆次数"].sum().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [int(v) for v in cls.values],
        "y": list(cls.index),
        "title": "各班级到馆次数排名 TOP 20",
        "x_label": "到馆次数",
        "y_label": "班级",
    }
    save_json("access_class_visits", data)


def compute_access_class_duration(df: pd.DataFrame):
    """1.3.4 各班级在馆时长排名 TOP 20"""
    cls = df.groupby("三级部门")["在馆时长(h)"].sum().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in cls.values],
        "y": list(cls.index),
        "title": "各班级在馆时长排名 TOP 20（小时）",
        "x_label": "时长（小时）",
        "y_label": "班级",
    }
    save_json("access_class_duration", data)


# =========================================================================
# ACCESS — STUDENT ANALYSIS (1.4.x)
# =========================================================================

def compute_access_student_top_visits(df: pd.DataFrame):
    """1.4.1-1 学生到馆总次数排名 TOP 20"""
    name_map = df.set_index("学号/工号")["姓名"].to_dict()
    stu = df.groupby("学号/工号")["到馆次数"].sum().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [int(v) for v in stu.values],
        "y": [f"{name_map.get(sid, sid)}" for sid in stu.index],
        "title": "学生到馆总次数排名 TOP 20",
        "x_label": "到馆次数",
        "y_label": "学生",
    }
    save_json("access_student_top_visits", data)


def compute_access_student_top_duration(df: pd.DataFrame):
    """1.4.1-2 学生在馆总时长排名 TOP 20"""
    name_map = df.set_index("学号/工号")["姓名"].to_dict()
    stu = df.groupby("学号/工号")["在馆时长(h)"].sum().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in stu.values],
        "y": [f"{name_map.get(sid, sid)}" for sid in stu.index],
        "title": "学生在馆总时长排名 TOP 20（小时）",
        "x_label": "时长（小时）",
        "y_label": "学生",
    }
    save_json("access_student_top_duration", data)


def compute_access_college_visit_boxplot(df: pd.DataFrame):
    """1.4.3 各学院到馆次数分布箱线图"""
    grouped = df.groupby(["一级部门", "学号/工号"]).size().reset_index(name="到馆总次数")
    colleges = sorted(grouped["一级部门"].unique())
    box_data = []
    for college in colleges:
        vals = sorted(grouped[grouped["一级部门"] == college]["到馆总次数"].tolist())
        box_data.append(vals)
    data = {
        "categories": colleges,
        "data": box_data,
        "title": "各学院学生到馆次数分布",
        "y_label": "到馆次数",
    }
    save_json("access_college_visit_boxplot", data)


def compute_access_college_duration_boxplot(df: pd.DataFrame):
    """1.4.4 各学院在馆时长分布箱线图"""
    grouped = df.groupby(["一级部门", "学号/工号"])["在馆时长(h)"].sum().reset_index()
    colleges = sorted(grouped["一级部门"].unique())
    box_data = []
    for college in colleges:
        vals = sorted(grouped[grouped["一级部门"] == college]["在馆时长(h)"].round(2).tolist())
        box_data.append(vals)
    data = {
        "categories": colleges,
        "data": box_data,
        "title": "各学院学生在馆时长分布（小时）",
        "y_label": "时长（小时）",
    }
    save_json("access_college_duration_boxplot", data)


def compute_access_scatter(df: pd.DataFrame):
    """1.4.5 学生到馆次数与在馆时长散点图 + 回归线"""
    grouped = df.groupby("学号/工号").agg(
        visits=("到馆次数", "sum"),
        duration=("在馆时长(h)", "sum"),
    ).reset_index()
    x = grouped["visits"].tolist()
    y = [round(v, 2) for v in grouped["duration"].tolist()]
    # Linear regression
    slope, intercept = np.polyfit(grouped["visits"], grouped["duration"], 1)
    x_line = [0, max(x)]
    y_line = [round(intercept, 2), round(slope * max(x) + intercept, 2)]
    data = {
        "x": [int(v) for v in x],
        "y": y,
        "regression": {
            "x": x_line,
            "y": y_line,
            "slope": round(float(slope), 3),
            "intercept": round(float(intercept), 3),
        },
        "title": "学生到馆次数与在馆时长关系",
        "x_label": "到馆次数",
        "y_label": "在馆时长（小时）",
    }
    save_json("access_scatter", data)


# =========================================================================
# BORROWING ANALYSIS
# =========================================================================

def compute_borrow_monthly(df_borrows: pd.DataFrame):
    """每月借书量趋势"""
    monthly = df_borrows.groupby(df_borrows["操作日期"].dt.to_period("M")).size()
    data = {
        "x": [str(p) for p in monthly.index],
        "y": [int(v) for v in monthly.values],
        "title": "每月借书量趋势",
        "x_label": "月份",
        "y_label": "借书量",
    }
    save_json("borrow_monthly", data)


def compute_borrow_hourly(df_borrows: pd.DataFrame):
    """每小时借书分布"""
    hourly = df_borrows.groupby("操作时段").size()
    data = {
        "x": [int(h) for h in hourly.index],
        "y": [int(v) for v in hourly.values],
        "title": "每小时借书分布",
        "x_label": "小时",
        "y_label": "借书量",
    }
    save_json("borrow_hourly", data)


def _merge_with_students(df_borrows: pd.DataFrame, df_students: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Merge borrows with students, handling type mismatch on join key."""
    left = df_borrows.copy()
    right = df_students[cols].copy()
    left["_join_key"] = left["读者证号"].astype(str)
    right["_join_key"] = right["学号"].astype(str)
    return left.merge(right[["_join_key"] + [c for c in cols if c != "学号"]], on="_join_key", how="left")


def compute_borrow_college(df_borrows: pd.DataFrame, df_students: pd.DataFrame):
    """各学院借阅量排名"""
    merged = _merge_with_students(df_borrows, df_students, ["学号", "学院"])
    college = merged.groupby("学院").size().sort_values(ascending=False)
    data = {
        "x": list(college.index),
        "y": [int(v) for v in college.values],
        "title": "各学院借阅量排名",
        "x_label": "学院",
        "y_label": "借阅量",
    }
    save_json("borrow_college", data)


def compute_borrow_college_per_capita(df_borrows: pd.DataFrame, df_students: pd.DataFrame):
    """各学院生均借阅量排名"""
    merged = _merge_with_students(df_borrows, df_students, ["学号", "学院"])
    total = merged.groupby("学院").size()
    students = merged.groupby("学院")["读者证号"].nunique()
    per_capita = (total / students).sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in per_capita.values],
        "y": list(per_capita.index),
        "title": "各学院生均借阅量排名",
        "x_label": "生均借阅量",
        "y_label": "学院",
    }
    save_json("borrow_college_per_capita", data)


def compute_borrow_major(df_borrows: pd.DataFrame, df_students: pd.DataFrame):
    """各专业借阅量排名 TOP 20"""
    merged = _merge_with_students(df_borrows, df_students, ["学号", "专业"])
    major = merged.groupby("专业").size().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [int(v) for v in major.values],
        "y": list(major.index),
        "title": "各专业借阅量排名 TOP 20",
        "x_label": "借阅量",
        "y_label": "专业",
    }
    save_json("borrow_major", data)


def compute_borrow_classifications(df_borrows: pd.DataFrame, df_cls: pd.DataFrame):
    """图书分类借阅量排名"""
    merged = df_borrows.merge(
        df_cls, left_on="主分类号", right_on="分类号", how="left"
    )
    cls = merged.groupby("分类名").size().sort_values(ascending=False)
    data = {
        "x": list(cls.index),
        "y": [int(v) for v in cls.values],
        "title": "图书分类借阅量排名",
        "x_label": "分类",
        "y_label": "借阅量",
    }
    save_json("borrow_classifications", data)


def compute_borrow_top_books(df_borrows: pd.DataFrame):
    """最受欢迎图书 TOP 20"""
    top = df_borrows.groupby("索书号").size().nlargest(20).sort_values(ascending=True)
    data = {
        "x": [int(v) for v in top.values],
        "y": list(top.index),
        "title": "最受欢迎图书 TOP 20（按索书号）",
        "x_label": "借阅次数",
        "y_label": "索书号",
    }
    save_json("borrow_top_books", data)


def compute_borrow_duration(df_borrows: pd.DataFrame):
    """借阅时长分布"""
    valid = df_borrows[df_borrows["有效借阅"] == 1]
    # Group into duration buckets
    bins = [0, 7, 14, 30, 60, 90, 150, 999]
    labels = ["≤7天", "8-14天", "15-30天", "31-60天", "61-90天", "91-150天", ">150天"]
    valid = valid.copy()
    valid["时长区间"] = pd.cut(valid["借阅时长"], bins=bins, labels=labels, right=True)
    dist = valid["时长区间"].value_counts().reindex(labels, fill_value=0)
    data = {
        "x": list(dist.index),
        "y": [int(v) for v in dist.values],
        "title": "借阅时长分布",
        "x_label": "时长区间",
        "y_label": "借阅次数",
    }
    save_json("borrow_duration", data)


def compute_borrow_college_duration(df_borrows: pd.DataFrame, df_students: pd.DataFrame):
    """各学院平均借阅时长"""
    merged = _merge_with_students(df_borrows, df_students, ["学号", "学院"])
    valid = merged[merged["有效借阅"] == 1]
    avg_dur = valid.groupby("学院")["借阅时长"].mean().sort_values(ascending=True)
    data = {
        "x": [round(float(v), 2) for v in avg_dur.values],
        "y": list(avg_dur.index),
        "title": "各学院平均借阅时长（天）",
        "x_label": "平均借阅时长（天）",
        "y_label": "学院",
    }
    save_json("borrow_college_duration", data)


# =========================================================================
# MAIN — Run all pre-computations
# =========================================================================

def main():
    print("=" * 50)
    print("NSU Library Dashboard — Pre-computing data...")
    print("=" * 50)

    print("\n[1/4] Loading data...")
    df_access = load_access()
    df_borrows = load_borrows()
    df_students = load_students()
    df_cls = load_classifications()
    print(f"  Access records: {len(df_access):,}")
    print(f"  Borrow records: {len(df_borrows):,}")
    print(f"  Students: {len(df_students):,}")

    print("\n[2/4] Computing overview...")
    compute_overview(df_access, df_borrows)

    print("\n[3/4] Computing access analysis...")
    compute_access_monthly_visits(df_access)
    compute_access_daily_visits(df_access)
    compute_access_weekday_visits(df_access)
    compute_access_hourly_visits(df_access)
    compute_access_monthly_duration(df_access)
    compute_access_monthly_avg_duration(df_access)
    compute_access_daily_duration(df_access)
    compute_access_daily_avg_duration(df_access)
    compute_access_weekday_duration(df_access)
    compute_access_weekday_avg_duration(df_access)
    compute_access_college_visits(df_access)
    compute_access_college_students(df_access)
    compute_access_college_duration(df_access)
    compute_access_college_avg_duration(df_access)
    compute_access_college_monthly_visits(df_access)
    compute_access_college_monthly_duration(df_access)
    compute_access_major_visits(df_access)
    compute_access_major_duration(df_access)
    compute_access_class_visits(df_access)
    compute_access_class_duration(df_access)
    compute_access_student_top_visits(df_access)
    compute_access_student_top_duration(df_access)
    compute_access_college_visit_boxplot(df_access)
    compute_access_college_duration_boxplot(df_access)
    compute_access_scatter(df_access)

    print("\n[4/4] Computing borrowing analysis...")
    compute_borrow_monthly(df_borrows)
    compute_borrow_hourly(df_borrows)
    compute_borrow_college(df_borrows, df_students)
    compute_borrow_college_per_capita(df_borrows, df_students)
    compute_borrow_major(df_borrows, df_students)
    compute_borrow_classifications(df_borrows, df_cls)
    compute_borrow_top_books(df_borrows)
    compute_borrow_duration(df_borrows)
    compute_borrow_college_duration(df_borrows, df_students)

    print("\n" + "=" * 50)
    print("Done! All JSON files saved to cache/")
    print("=" * 50)


if __name__ == "__main__":
    main()
