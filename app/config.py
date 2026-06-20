"""
Configuration for NSU Library Dashboard.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = BASE_DIR / "cache"

# Data file paths
ACCESS_RECORDS_FILE = DATA_DIR / "access records.xlsx"
BORROWS_FILE = DATA_DIR / "borrows.xlsx"
RETURNS_FILE = DATA_DIR / "returns.xlsx"
STUDENTS_FILE = DATA_DIR / "students.xlsx"
BOOK_CLASSIFICATIONS_FILE = DATA_DIR / "bookclassifications.xlsx"

# Server settings (支持环境变量覆盖，方便生产部署)
HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.getenv("DASHBOARD_PORT", "8000"))

# Data period
DATA_START = "2023-10-31"
DATA_END = "2024-06-30"
