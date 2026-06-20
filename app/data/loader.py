"""
Data loader — loads Excel files into pandas DataFrames with caching.
Each loader returns a processed DataFrame ready for aggregation.
"""
import pandas as pd
from functools import lru_cache
from app.config import (
    ACCESS_RECORDS_FILE, BORROWS_FILE, RETURNS_FILE,
    STUDENTS_FILE, BOOK_CLASSIFICATIONS_FILE,
)

# ---------------------------------------------------------------------------
# Access records (到馆数据)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_access() -> pd.DataFrame:
    """Load and process access records. ~399K student rows."""
    df = pd.read_excel(ACCESS_RECORDS_FILE, sheet_name="Sheet1")
    # Filter to students only
    df = df[df["读者类型"] == "学生"].copy()
    # Convert dates & set index
    df["进馆日期"] = pd.to_datetime(df["进馆日期"])
    df.set_index("进馆日期", inplace=True)
    # Convert entry time for hour extraction
    df["进馆时间"] = pd.to_datetime(df["进馆时间"], format="mixed")
    df["hour"] = df["进馆时间"].dt.hour
    df["weekday"] = df.index.dayofweek  # 0=Mon, 6=Sun
    df["day_of_month"] = df.index.day
    return df

# ---------------------------------------------------------------------------
# Borrowing records (借书数据)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_borrows() -> pd.DataFrame:
    """Load borrow records."""
    df = pd.read_excel(BORROWS_FILE)
    df["操作日期"] = pd.to_datetime(df["操作日期"])
    return df

# ---------------------------------------------------------------------------
# Return records (还书数据)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_returns() -> pd.DataFrame:
    """Load return records."""
    df = pd.read_excel(RETURNS_FILE)
    df["操作日期"] = pd.to_datetime(df["操作日期"])
    return df

# ---------------------------------------------------------------------------
# Student info (学生信息)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_students() -> pd.DataFrame:
    """Load student master list."""
    return pd.read_excel(STUDENTS_FILE)

# ---------------------------------------------------------------------------
# Book classifications (图书分类)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_classifications() -> pd.DataFrame:
    """Load book classification lookup table."""
    return pd.read_excel(BOOK_CLASSIFICATIONS_FILE)
