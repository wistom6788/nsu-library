"""
缓存读取服务 —— 统一加载预计算 JSON，避免在各路由中重复实现。
"""
import json
from app.config import CACHE_DIR


def load_cached(name: str) -> dict:
    """读取 cache 目录下的预计算 JSON 文件。

    Args:
        name: 文件名（不含 .json 后缀）。

    Returns:
        解析后的字典；文件不存在或解析失败时返回空字典，
        保证调用方在缓存缺失时仍能拿到稳定结构。
    """
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 缓存损坏时返回空字典，避免单点故障导致接口 500
        return {}
