"""
NSU Library Dashboard — FastAPI Application
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import HOST, PORT
from app.routers import overview, access, borrowing, student

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NSU Library Dashboard",
    description="成都东软学院图书馆数据分析看板",
    version="1.0.0",
)

# Static files & templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Share templates with routers
app.state.templates = templates

# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------

app.include_router(overview.router)
app.include_router(access.router)
app.include_router(borrowing.router)
app.include_router(student.router)

# ---------------------------------------------------------------------------
# Startup event — check cache exists
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    cache_dir = BASE_DIR.parent / "cache"
    if not any(cache_dir.glob("*.json")):
        print("[WARN] No cached data found. Run: python -m app.data.precompute")
    else:
        count = len(list(cache_dir.glob("*.json")))
        print(f"[OK] Loaded {count} cached data files")
