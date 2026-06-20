"""
build_static.py — 将 FastAPI 动态站点构建为纯静态站点（适配 Netlify 部署）

用法：
    python build_static.py

输出：dist/ 目录，可直接部署到 Netlify / Vercel / GitHub Pages 等静态托管平台。
"""

import json
import os
import shutil
import ssl
import urllib.request
from pathlib import Path

# ── 项目路径 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
CACHE_DIR = PROJECT_ROOT / "cache"
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
STATIC_SRC = PROJECT_ROOT / "app" / "static"
DIST_DIR = PROJECT_ROOT / "dist"

# ── ECharts CDN ───────────────────────────────────────────
ECHARTS_URL = "https://assets.pyecharts.org/assets/echarts.min.js"
VENDOR_DIR = DIST_DIR / "static" / "vendor"


# ══════════════════════════════════════════════════════════
#  1. 工具函数
# ══════════════════════════════════════════════════════════


def load_cache(name: str) -> dict:
    """读取缓存 JSON，文件不存在返回空字典。"""
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        print(f"  [WARN] 缓存缺失: {path.name}")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def copy_static():
    """复制 static 资源到 dist/static/。"""
    dst = DIST_DIR / "static"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(STATIC_SRC, dst)
    print(f"  已复制 static/ → {dst}")


def download_echarts():
    """下载 ECharts 到本地 vendor 目录，确保离线可用。"""
    ensure_dir(VENDOR_DIR)
    target = VENDOR_DIR / "echarts.min.js"
    if target.exists() and target.stat().st_size > 0:
        print(f"  ECharts 已存在 ({target.stat().st_size:,} bytes)")
        return
    # 备选 CDN 源
    urls = [
        "https://assets.pyecharts.org/assets/echarts.min.js",
        "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js",
        "https://unpkg.com/echarts@5.4.3/dist/echarts.min.js",
    ]
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for url in urls:
        try:
            print(f"  正在下载 ECharts: {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                data = resp.read()
                target.write_bytes(data)
            size = target.stat().st_size
            if size > 10000:  # 合理的最小文件大小
                print(f"  ECharts 下载完成 ({size:,} bytes)")
                return
            else:
                target.unlink(missing_ok=True)
                print(f"  文件过小，尝试下一个源...")
        except Exception as e:
            print(f"  下载失败 ({url}): {e}")
    raise RuntimeError("所有 ECharts CDN 源均无法访问，请手动下载 echarts.min.js 放入 dist/static/vendor/")


# ══════════════════════════════════════════════════════════
#  2. 页面数据组装
# ══════════════════════════════════════════════════════════


def build_overview_data() -> dict:
    """总览页所需数据。"""
    return {
        "_page": "overview",
        "kpi": load_cache("overview"),
        "charts": {
            "monthly_visits": load_cache("access_monthly_visits"),
            "college_visits": load_cache("access_college_visits"),
            "borrow_monthly": load_cache("borrow_monthly"),
        },
    }


def build_access_data() -> dict:
    """到馆分析页所需数据（全部 API 数据）。"""
    return {
        "_page": "access",
        "time": {
            "monthly_visits": load_cache("access_monthly_visits"),
            "daily_visits": load_cache("access_daily_visits"),
            "weekday_visits": load_cache("access_weekday_visits"),
            "hourly_visits": load_cache("access_hourly_visits"),
            "monthly_duration": load_cache("access_monthly_duration"),
            "monthly_avg_duration": load_cache("access_monthly_avg_duration"),
            "daily_duration": load_cache("access_daily_duration"),
            "daily_avg_duration": load_cache("access_daily_avg_duration"),
            "weekday_duration": load_cache("access_weekday_duration"),
            "weekday_avg_duration": load_cache("access_weekday_avg_duration"),
        },
        "college": {
            "visits": load_cache("access_college_visits"),
            "students": load_cache("access_college_students"),
            "duration": load_cache("access_college_duration"),
            "avg_duration": load_cache("access_college_avg_duration"),
            "monthly_visits": load_cache("access_college_monthly_visits"),
            "monthly_duration": load_cache("access_college_monthly_duration"),
        },
        "major": {
            "major_visits": load_cache("access_major_visits"),
            "major_duration": load_cache("access_major_duration"),
            "class_visits": load_cache("access_class_visits"),
            "class_duration": load_cache("access_class_duration"),
        },
        "student": {
            "top_visits": load_cache("access_student_top_visits"),
            "top_duration": load_cache("access_student_top_duration"),
            "visit_boxplot": load_cache("access_college_visit_boxplot"),
            "duration_boxplot": load_cache("access_college_duration_boxplot"),
            "scatter": load_cache("access_scatter"),
        },
    }


def build_borrowing_data() -> dict:
    """借阅分析页所需数据。"""
    return {
        "_page": "borrowing",
        "monthly": load_cache("borrow_monthly"),
        "hourly": load_cache("borrow_hourly"),
        "college": load_cache("borrow_college"),
        "per_capita": load_cache("borrow_college_per_capita"),
        "major": load_cache("borrow_major"),
        "classifications": load_cache("borrow_classifications"),
        "top_books": load_cache("borrow_top_books"),
        "duration": load_cache("borrow_duration"),
        "college_duration": load_cache("borrow_college_duration"),
    }


def build_student_index() -> list:
    """
    从 students.xlsx 提取学生索引，供客户端搜索使用。
    返回 [{student_id, name, college, major, class_name}, ...]
    """
    import pandas as pd
    students_path = PROJECT_ROOT / "data" / "students.xlsx"
    if not students_path.exists():
        print(f"  [WARN] 学生数据不存在: {students_path}")
        return []
    df = pd.read_excel(students_path)
    results = []
    for _, row in df.iterrows():
        results.append({
            "student_id": str(row["学号"]),
            "name": row["姓名"],
            "college": row["学院"],
            "major": row["专业"],
            "class_name": row["行政班号"],
        })
    print(f"  学生索引: {len(results)} 条记录")
    return results


# ══════════════════════════════════════════════════════════
#  3. HTML 模板渲染（纯字符串拼接，无 Jinja2 依赖）
# ══════════════════════════════════════════════════════════


BASE_HTML_TEMPLATE = '''\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="/static/css/style.css">
    <link rel="stylesheet" href="/static/css/style-vibrant.css">
</head>
<body>
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-header">
            <h2>&#128218; NSU 图书馆</h2>
            <p class="sidebar-subtitle">数据分析看板</p>
        </div>
        <nav class="sidebar-nav">
            <a href="/" class="nav-item {active_overview}">&#128202; <span class="nav-text">总览</span></a>
            <a href="/access.html" class="nav-item {active_access}">&#128682; <span class="nav-text">到馆分析</span></a>
            <a href="/borrowing.html" class="nav-item {active_borrowing}">&#128214; <span class="nav-text">借阅分析</span></a>
            <a href="/student.html" class="nav-item {active_student}">&#128100; <span class="nav-text">学生查询</span></a>
        </nav>
        <div class="theme-switcher" id="themeSwitcher" title="切换界面风格">
            <span class="switch-icon">&#127912;</span>
            <span>切换风格</span>
        </div>
        <div class="sidebar-footer">
            <p>数据区间：2023.10 - 2024.06</p>
            <p>成都东软学院</p>
        </div>
    </aside>

    <!-- Main content -->
    <main class="main-content">
{content}
    </main>

    <script src="/static/vendor/echarts.min.js"></script>
    <script src="/static/js/charts.js"></script>
    <script src="/static/js/app-static.js"></script>
    <script>
// 内嵌页面数据（替代 API 请求）
var PAGE_DATA = {data_json};
    </script>
    <script>{init_script}</script>
    <script>
        // 主题切换逻辑
        (function(){{
            var KEY='nsu_theme',switcher=document.getElementById('themeSwitcher');
            if(!switcher)return;
            function apply(t){{
                if(t==='vibrant'){{document.body.setAttribute('data-theme','vibrant');switcher.querySelector('.switch-icon').textContent='\U0001F3A8';}}
                else{{document.body.removeAttribute('data-theme');switcher.querySelector('.switch-icon').textContent='\U0001F3A6';}}
            }}
            var saved=localStorage.getItem(KEY);apply(saved||'default');
            switcher.addEventListener('click',function(){{
                var cur=document.body.getAttribute('data-theme');
                var nxt=cur==='vibrant'?'default':'vibrant';
                localStorage.setItem(KEY,nxt);apply(nxt);
            }});
        }})();
    </script>
</body>
</html>\
'''


def render_page(title: str, active_page: str, content_html: str,
                data: dict, init_script: str) -> str:
    """用内嵌数据渲染完整页面。"""
    actives = {k: ("active" if k == active_page else "") for k in
               ["overview", "access", "borrowing", "student"]}
    return BASE_HTML_TEMPLATE.format(
        title=title,
        active_overview=actives["overview"],
        active_access=actives["access"],
        active_borrowing=actives["borrowing"],
        active_student=actives["student"],
        content=content_html,
        data_json=json.dumps(data, ensure_ascii=False),
        init_script=init_script,
    )


# ── 各页面内容片段 ────────────────────────────────────────

OVERVIEW_CONTENT = '''\
<div class="page-header">
    <h1>&#128202; 数据总览</h1>
    <p>成都东软学院图书馆 2023年10月 — 2024年6月</p>
</div>

<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-icon">&#128682;</div>
        <div class="kpi-content">
            <div class="kpi-value" id="kpi-visits">&mdash;</div>
            <div class="kpi-label">总到馆人次</div>
        </div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">&#128214;</div>
        <div class="kpi-content">
            <div class="kpi-value" id="kpi-borrows">&mdash;</div>
            <div class="kpi-label">总借书量</div>
        </div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">&#9201;&#65039;</div>
        <div class="kpi-content">
            <div class="kpi-value" id="kpi-duration">&mdash;</div>
            <div class="kpi-label">平均在馆时长(h)</div>
        </div>
    </div>
</div>

<div class="chart-grid-2">
    <div class="chart-card"><div id="chart-monthly-visits" class="chart-container"></div></div>
    <div class="chart-card"><div id="chart-college-visits" class="chart-container"></div></div>
</div>
<div class="chart-grid-1">
    <div class="chart-card"><div id="chart-borrow-monthly" class="chart-container"></div></div>
</div>'''

ACCESS_CONTENT = '''\
<div class="page-header">
    <h1>&#128682; 到馆数据分析</h1>
    <p>学生进馆记录的多维度分析</p>
</div>

<div class="tab-nav">
    <button class="tab-btn active" data-tab="time">&#9201;&#65039; 时间分析</button>
    <button class="tab-btn" data-tab="college">&#127979; 学院分析</button>
    <button class="tab-btn" data-tab="major">&#128218; 专业/班级</button>
    <button class="tab-btn" data-tab="student">&#128100; 学生分析</button>
</div>

<div class="tab-content active" id="tab-time">
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-monthly-visits" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-daily-visits" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-weekday-visits" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-hourly-visits" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-monthly-duration" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-monthly-avg-duration" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-daily-duration" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-daily-avg-duration" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-weekday-duration" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-weekday-avg-duration" class="chart-container"></div></div>
    </div>
</div>

<div class="tab-content" id="tab-college">
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-college-visits" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-college-students" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-college-duration" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-college-avg-duration" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-college-monthly-visits" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-college-monthly-duration" class="chart-container"></div></div>
    </div>
</div>

<div class="tab-content" id="tab-major">
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-major-visits" class="chart-container-lg"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-major-duration" class="chart-container-lg"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-class-visits" class="chart-container-lg"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-class-duration" class="chart-container-lg"></div></div>
    </div>
</div>

<div class="tab-content" id="tab-student">
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-student-top-visits" class="chart-container-lg"></div></div>
        <div class="chart-card"><div id="chart-student-top-duration" class="chart-container-lg"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-visit-boxplot" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-duration-boxplot" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-scatter" class="chart-container-lg"></div></div>
    </div>
</div>'''

BORROWING_CONTENT = '''\
<div class="page-header">
    <h1>&#128214; 借阅数据分析</h1>
    <p>图书借还记录的多维度分析</p>
</div>

<div class="tab-nav">
    <button class="tab-btn active" data-tab="borrow-overview">&#128200; 借阅概览</button>
    <button class="tab-btn" data-tab="borrow-rank">&#127942; 排行榜</button>
    <button class="tab-btn" data-tab="borrow-book">&#128218; 图书分析</button>
    <button class="tab-btn" data-tab="borrow-duration">&#9203; 时长分析</button>
</div>

<div class="tab-content active" id="tab-borrow-overview">
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-borrow-monthly" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-borrow-hourly" class="chart-container"></div></div>
    </div>
</div>

<div class="tab-content" id="tab-borrow-rank">
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-borrow-college" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-borrow-college-per-capita" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-borrow-major" class="chart-container-lg"></div></div>
    </div>
</div>

<div class="tab-content" id="tab-borrow-book">
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-borrow-classifications" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-1">
        <div class="chart-card"><div id="chart-borrow-top-books" class="chart-container-lg"></div></div>
    </div>
</div>

<div class="tab-content" id="tab-borrow-duration">
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-borrow-duration" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-borrow-college-duration" class="chart-container"></div></div>
    </div>
</div>'''

STUDENT_CONTENT = '''\
<div class="page-header">
    <h1>&#128100; 学生查询</h1>
    <p>输入学号或姓名搜索学生，查看个人图书馆使用详情</p>
</div>

<div class="search-container">
    <div class="search-box">
        <input type="text" id="student-search" placeholder="输入学号或姓名搜索..." autocomplete="off">
        <button id="search-btn" onclick="searchStudentStatic()">&#128269; 搜索</button>
    </div>
    <div id="search-results" class="search-results"></div>
</div>

<div id="student-detail" class="student-detail" style="display:none;">
    <div class="student-info-card">
        <div class="student-avatar">&#128100;</div>
        <div class="student-info-text">
            <h2 id="stu-name">&mdash;</h2>
            <p><strong>学号：</strong><span id="stu-id">&mdash;</span></p>
            <p><strong>学院：</strong><span id="stu-college">&mdash;</span></p>
            <p><strong>专业：</strong><span id="stu-major">&mdash;</span></p>
            <p><strong>班级：</strong><span id="stu-class">&mdash;</span></p>
        </div>
    </div>
    <div class="kpi-grid" id="student-kpis"></div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-stu-monthly-visits" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-stu-hourly-visits" class="chart-container"></div></div>
    </div>
    <div class="chart-grid-2">
        <div class="chart-card"><div id="chart-stu-weekday-visits" class="chart-container"></div></div>
        <div class="chart-card"><div id="chart-stu-monthly-borrows" class="chart-container"></div></div>
    </div>
</div>'''


# ══════════════════════════════════════════════════════════
#  4. 主构建流程
# ══════════════════════════════════════════════════════════


def main():
    print("=" * 50)
    print("  NSU Library Dashboard — 静态站点构建")
    print("=" * 50)

    # 清理旧构建
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    ensure_dir(DIST_DIR)

    # ── Step 1: 复制静态资源 & 下载 ECharts ──────────────
    print("\n[1/5] 准备静态资源...")
    copy_static()
    download_echarts()

    # ── Step 2: 构建各页面数据 ─────────────────────────
    print("\n[2/5] 组装页面数据...")
    overview_data = build_overview_data()
    access_data = build_access_data()
    borrowing_data = build_borrowing_data()
    student_list = build_student_index()

    # ── Step 3: 渲染 HTML 页面 ─────────────────────────
    print("\n[3/5] 渲染 HTML 页面...")

    # 首页 index.html
    html_index = render_page(
        title="总览 — NSU Library Dashboard",
        active_page="overview",
        content_html=OVERVIEW_CONTENT,
        data=overview_data,
        init_script="initOverviewStatic();",
    )
    (DIST_DIR / "index.html").write_text(html_index, encoding="utf-8")
    print("  ✓ index.html")

    # 到馆分析 access.html
    html_access = render_page(
        title="到馆分析 — NSU Library Dashboard",
        active_page="access",
        content_html=ACCESS_CONTENT,
        data=access_data,
        init_script="initAccessStatic();initTabs();",
    )
    (DIST_DIR / "access.html").write_text(html_access, encoding="utf-8")
    print("  ✓ access.html")

    # 借阅分析 borrowing.html
    html_borrowing = render_page(
        title="借阅分析 — NSU Library Dashboard",
        active_page="borrowing",
        content_html=BORROWING_CONTENT,
        data=borrowing_data,
        init_script="initBorrowingStatic();initTabs();",
    )
    (DIST_DIR / "borrowing.html").write_text(html_borrowing, encoding="utf-8")
    print("  ✓ borrowing.html")

    # 学生查询 student.html
    student_data = {"_page": "student", "students": student_list}
    html_student = render_page(
        title="学生查询 — NSU Library Dashboard",
        active_page="student",
        content_html=STUDENT_CONTENT,
        data=student_data,
        init_script="initStudentStatic();",
    )
    (DIST_DIR / "student.html").write_text(html_student, encoding="utf-8")
    print("  ✓ student.html")

    # ── Step 4: 创建 app-static.js ──────────────────────
    print("\n[4/5] 生成 app-static.js...")
    create_app_static_js()

    # ── Step 5: 创建 Netlify 配置 ───────────────────────
    print("\n[5/5] 生成部署配置...")
    create_netlify_config()

    # 统计
    total_files = sum(1 for _ in DIST_DIR.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in DIST_DIR.rglob("*") if f.is_file())

    print(f"\n{'=' * 50}")
    print(f"  构建完成！")
    print(f"  输出目录: {DIST_DIR}")
    print(f"  文件数量: {total_files}")
    print(f"  总大小:   {total_size / 1024 / 1024:.1f} MB")
    print(f"{'=' * 50}")
    print(f"\n  部署方式:")
    print(f"  1. 将 {DIST_DIR.name}/ 文件夹上传至 Netlify")
    print(f"  2. 或连接 Git 仓库，设置发布目录为: dist")
    print(f"  3. 或运行: ntl deploy --dir=dist --prod")


def create_app_static_js():
    """
    创建 app-static.js，替代原 app.js 的 fetchJSON 调用，
    改为从全局变量 PAGE_DATA 中同步读取数据。
    """

    js_content = '''/**
 * app-static.js — 静态版本页面初始化
 * 从内嵌的 PAGE_DATA 全局变量中读取数据，无需后端 API。
 */

// ── TAB SYSTEM ──────────────────────────────────────────

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var tabId = this.getAttribute('data-tab');
            // Update buttons
            var nav = this.closest('.tab-nav');
            nav.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            // Update content
            document.querySelectorAll('.tab-content').forEach(function(c) { c.classList.remove('active'); });
            var content = document.getElementById('tab-' + tabId);
            if (content) {
                content.classList.add('active');
                // Resize all charts in the newly visible tab
                setTimeout(function() {
                    content.querySelectorAll('[id^="chart-"]').forEach(function(dom) {
                        var inst = echarts.getInstanceByDom(dom);
                        if (inst) inst.resize();
                    });
                }, 50);
            }
        });
    });
}

// ── DATA RESOLVER ────────────────────────────────────────

function fetchJSON(url) {
    // 静态版本：从 PAGE_DATA 同步获取数据，忽略 URL 参数
    // 兼容原有调用方式，但不再发起网络请求
    const d = PAGE_DATA || {};
    // 根据 page 类型分发
    if (d._page === 'overview') return Promise.resolve(d.kpi);
    if (d._page === 'access') return resolveAccessData(url);
    if (d._page === 'borrowing') return resolveBorrowingData(url);
    return Promise.resolve({});
}

function resolveAccessData(url) {
    const map = {
        '/api/access/monthly-visits': 'time.monthly_visits',
        '/api/access/daily-visits': 'time.daily_visits',
        '/api/access/weekday-visits': 'time.weekday_visits',
        '/api/access/hourly-visits': 'time.hourly_visits',
        '/api/access/monthly-duration': 'time.monthly_duration',
        '/api/access/monthly-avg-duration': 'time.monthly_avg_duration',
        '/api/access/daily-duration': 'time.daily_duration',
        '/api/access/daily-avg-duration': 'time.daily_avg_duration',
        '/api/access/weekday-duration': 'time.weekday_duration',
        '/api/access/weekday-avg-duration': 'time.weekday_avg_duration',
        '/api/access/college-visits': 'college.visits',
        '/api/access/college-students': 'college.students',
        '/api/access/college-duration': 'college.duration',
        '/api/access/college-avg-duration': 'college.avg_duration',
        '/api/access/college-monthly-visits': 'college.monthly_visits',
        '/api/access/college-monthly-duration': 'college.monthly_duration',
        '/api/access/major-visits': 'major.major_visits',
        '/api/access/major-duration': 'major.major_duration',
        '/api/access/class-visits': 'major.class_visits',
        '/api/access/class-duration': 'major.class_duration',
        '/api/access/student-top-visits': 'student.top_visits',
        '/api/access/student-top-duration': 'student.top_duration',
        '/api/access/college-visit-boxplot': 'student.visit_boxplot',
        '/api/access/college-duration-boxplot': 'student.duration_boxplot',
        '/api/access/scatter': 'student.scatter',
    };
    const path = getNested(PAGE_DATA, map[url] || '');
    return Promise.resolve(path || {});
}

function resolveBorrowingData(url) {
    const map = {
        '/api/borrowing/monthly': 'monthly',
        '/api/borrowing/hourly': 'hourly',
        '/api/borrowing/college': 'college',
        '/api/borrowing/college-per-capita': 'per_capita',
        '/api/borrowing/major': 'major',
        '/api/borrowing/classifications': 'classifications',
        '/api/borrowing/top-books': 'top_books',
        '/api/borrowing/duration': 'duration',
        '/api/borrowing/college-duration': 'college_duration',
    };
    const path = getNested(PAGE_DATA, map[url] || '');
    return Promise.resolve(path || {});
}

/** 通过点分路径从嵌套对象取值 */
function getNested(obj, pathStr) {
    if (!pathStr) return obj;
    return pathStr.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : null), obj);
}

// ── OVERVIEW ────────────────────────────────────────────

async function initOverviewStatic() {
    const kpi = PAGE_DATA.kpi || {};
    animateKPI('kpi-visits', kpi.total_visits);
    animateKPI('kpi-borrows', kpi.total_borrows);
    animateKPI('kpi-duration', kpi.avg_duration_h);

    const charts = PAGE_DATA.charts || {};

    const c1 = initChart('chart-monthly-visits');
    if (c1) { registerChart(c1); renderBar(c1, charts.monthly_visits); }

    const c2 = initChart('chart-college-visits');
    if (c2) { registerChart(c2); renderBar(c2, charts.college_visits); }

    const c3 = initChart('chart-borrow-monthly');
    if (c3) { registerChart(c3); renderBar(c3, charts.borrow_monthly); }
}

// ── ACCESS ───────────────────────────────────────────────

async function initAccessStatic() {
    await loadAccessTime();
}

async function loadAccessTime() {
    const t = PAGE_DATA.time || {};
    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-monthly-visits', t.monthly_visits, renderBar);
    makeChart('chart-daily-visits', t.daily_visits, (c, d) => renderLine(c, d, { area: true }));
    makeChart('chart-weekday-visits', t.weekday_visits, renderBar);
    makeChart('chart-hourly-visits', t.hourly_visits, (c, d) => renderLine(c, d, { smooth: true }));
    makeChart('chart-monthly-duration', t.monthly_duration, renderBar);
    makeChart('chart-monthly-avg-duration', t.monthly_avg_duration, renderBar);
    makeChart('chart-daily-duration', t.daily_duration, (c, d) => renderLine(c, d, { area: true }));
    makeChart('chart-daily-avg-duration', t.daily_avg_duration, renderBar);
    makeChart('chart-weekday-duration', t.weekday_duration, renderBar);
    makeChart('chart-weekday-avg-duration', t.weekday_avg_duration, renderBar);

    // 学院、专业、学生 tab 数据也一次性加载（已全部在 PAGE_DATA 中）
    const col = PAGE_DATA.college || {};
    makeChart('chart-college-visits', col.visits, renderBar);
    makeChart('chart-college-students', col.students, renderBar);
    makeChart('chart-college-duration', col.duration, renderHorizontalBar);
    makeChart('chart-college-avg-duration', col.avg_duration, renderHorizontalBar);
    makeChart('chart-college-monthly-visits', col.monthly_visits, renderMultiLine);
    makeChart('chart-college-monthly-duration', col.monthly_duration, renderMultiLine);

    const maj = PAGE_DATA.major || {};
    makeChart('chart-major-visits', maj.major_visits, renderHorizontalBar);
    makeChart('chart-major-duration', maj.major_duration, renderHorizontalBar);
    makeChart('chart-class-visits', maj.class_visits, renderHorizontalBar);
    makeChart('chart-class-duration', maj.class_duration, renderHorizontalBar);

    const stu = PAGE_DATA.student || {};
    makeChart('chart-student-top-visits', stu.top_visits, renderHorizontalBar);
    makeChart('chart-student-top-duration', stu.top_duration, renderHorizontalBar);
    makeChart('chart-visit-boxplot', stu.visit_boxplot, renderBoxplot);
    makeChart('chart-duration-boxplot', stu.duration_boxplot, renderBoxplot);
    makeChart('chart-scatter', stu.scatter, renderScatter);
}

// ── BORROWING ───────────────────────────────────────────

async function initBorrowingStatic() {
    const d = PAGE_DATA || {};
    const makeChart = (id, data, renderFn) => {
        const c = initChart(id);
        if (c) { registerChart(c); renderFn(c, data); }
    };

    makeChart('chart-borrow-monthly', d.monthly, renderBar);
    makeChart('chart-borrow-hourly', d.hourly, (c, v) => renderLine(c, v, { smooth: true }));
    makeChart('chart-borrow-college', d.college, renderBar);
    makeChart('chart-borrow-college-per-capita', d.per_capita, renderHorizontalBar);
    makeChart('chart-borrow-major', d.major, renderHorizontalBar);
    makeChart('chart-borrow-classifications', d.classifications, renderBar);
    makeChart('chart-borrow-top-books', d.top_books, renderHorizontalBar);
    makeChart('chart-borrow-duration', d.duration, renderBar);
    makeChart('chart-borrow-college-duration', d.college_duration, renderHorizontalBar);
}

// ── STUDENT (客户端搜索) ─────────────────────────────────

var _studentIndex = null;

function initStudentStatic() {
    _studentIndex = (PAGE_DATA.students || []).map(function(s) {
        return {
            student_id: String(s.student_id || ''),
            name: String(s.name || ''),
            college: String(s.college || ''),
            major: String(s.major || ''),
            class_name: String(s.class_name || ''),
            _searchKey: (String(s.student_id || '') + ' ' + String(s.name || '')).toLowerCase()
        };
    });
    document.getElementById('student-search').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') searchStudentStatic();
    });
    let timer;
    document.getElementById('student-search').addEventListener('input', function() {
        clearTimeout(timer);
        timer = setTimeout(function() {
            if (this.value.length >= 1) searchStudentStatic();
        }.bind(this), 300);
    });
}

function searchStudentStatic() {
    var query = document.getElementById('student-search').value.trim().toLowerCase();
    if (!query || !_studentIndex) return;

    var resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '<div class="search-loading">搜索中...</div>';

    var matches = _studentIndex.filter(function(s) {
        return s._searchKey.indexOf(query) !== -1;
    }).slice(0, 20);

    if (matches.length === 0) {
        resultsDiv.innerHTML = '<div class="search-empty">未找到匹配的学生</div>';
        return;
    }

    var html = '<div class="search-list">';
    matches.forEach(function(stu) {
        html += '<div class="search-item" onclick="showStudentInfo(' + JSON.stringify(stu).replace(/"/g, '&quot;') + ')">' +
            '<span class="search-name">' + escapeHtml(stu.name) + '</span>' +
            '<span class="search-id">' + escapeHtml(stu.student_id) + '</span>' +
            '<span class="search-college">' + escapeHtml(stu.college) + '</span>' +
            '<span class="search-major">' + escapeHtml(stu.major) + '</span>' +
            '</div>';
    });
    html += '</div>';
    resultsDiv.innerHTML = html;
}

function showStudentInfo(stu) {
    var detailDiv = document.getElementById('student-detail');
    var resultsDiv = document.getElementById('search-results');
    resultsDiv.innerHTML = '';
    detailDiv.style.display = 'block';

    document.getElementById('stu-name').textContent = stu.name;
    document.getElementById('stu-id').textContent = stu.student_id;
    document.getElementById('stu-college').textContent = stu.college;
    document.getElementById('stu-major').textContent = stu.major;
    document.getElementById('stu-class').textContent = stu.class_name;

    // KPI 占位（静态版无法提供实时统计，显示提示）
    var kpiDiv = document.getElementById('student-kpis');
    kpiDiv.innerHTML =
        '<div class="kpi-card"><div class="kpi-icon">&#128682;</div><div class="kpi-content"><div class="kpi-value">' + escapeHtml(stu.college) + '</div><div class="kpi-label">所属学院</div></div></div>' +
        '<div class="kpi-card"><div class="kpi-icon">&#128218;</div><div class="kpi-content"><div class="kpi-value">' + escapeHtml(stu.major) + '</div><div class="kpi-label">所属专业</div></div></div>' +
        '<div class="kpi-card"><div class="kpi-icon">&#127891;</div><div class="kpi-content"><div class="kpi-value">' + escapeHtml(stu.class_name) + '</div><div class="kpi-label">班级</div></div></div>' +
        '<div class="kpi-card"><div class="kpi-icon">&#128100;</div><div class="kpi-content"><div class="kpi-value">' + escapeHtml(stu.name) + '</div><div class="kpi-label">学生姓名</div></div></div>';

    // 清空图表容器（静态版无个人详细统计数据）
    ['chart-stu-monthly-visits','chart-stu-hourly-visits',
     'chart-stu-weekday-visits','chart-stu-monthly-borrows'].forEach(function(id) {
        var dom = document.getElementById(id);
        if (dom) dom.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;">详细统计需后端支持</div>';
    });
}

function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}
'''
    js_path = DIST_DIR / "static" / "js" / "app-static.js"
    js_path.write_text(js_content, encoding="utf-8")
    print(f"  ✓ app-static.js")


def create_netlify_config():
    """创建 netlify.toml 和 redirects 配置。"""

    # netlify.toml
    toml = '''[build]
  publish = "dist"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    Cache-Control = "public, max-age=3600"

[[headers]]
  for = "/static/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
'''
    (DIST_DIR / "netlify.toml").write_text(toml, encoding="utf-8")

    # _redirects (Netlify SPA fallback)
    redirects = '''/              /index.html    200
/access.html    /access.html    200
/borrowing.html /borrowing.html 200
/student.html   /student.html   200
'''
    (DIST_DIR / "_redirects").write_text(redirects, encoding="utf-8")

    print(f"  ✓ netlify.toml")
    print(f"  ✓ _redirects")


if __name__ == "__main__":
    main()
