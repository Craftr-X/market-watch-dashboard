from __future__ import annotations

import time
from datetime import date
from functools import wraps

import akshare as ak
import pandas as pd


# 需要跟踪的主要指数
TRACKED_INDICES = {
    "000001": "上证指数",
    "399001": "深证成指",
    "399006": "创业板指",
    "000300": "沪深300",
    "000510": "中证A500",
    "000905": "中证500",
}


def retry(max_retries=3, delay=1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"[Retry] {func.__name__} attempt {attempt + 1} failed: {e}")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator


def load_market_data(trading_day: date | None = None) -> dict:
    """从 AkShare 获取真实 A 股数据"""
    day = (trading_day or date.today()).isoformat()

    try:
        # 1. 获取指数数据
        indices = _fetch_indices()

        # 2. 获取行业板块数据
        sectors = _fetch_sectors()

        # 3. 获取个股数据
        stocks = _fetch_stocks()

        return {
            "date": day,
            "source": "akshare",
            "indices": indices,
            "sectors": sectors,
            "stocks": stocks,
        }
    except Exception as e:
        # 如果获取失败，返回空数据并记录错误
        print(f"[AkShare Error] {e}")
        return {
            "date": day,
            "source": "akshare-error",
            "indices": [],
            "sectors": [],
            "stocks": [],
        }


@retry(max_retries=3, delay=2)
def _fetch_indices() -> list[dict]:
    """获取主要指数行情"""
    try:
        # 使用新浪接口（更稳定）
        df = ak.stock_zh_index_spot_sina()

        indices = []
        for code, name in TRACKED_INDICES.items():
            # 新浪接口代码格式：sh000001 或 sz399001
            sina_code = f"sh{code}" if code.startswith("0") else f"sz{code}"
            row = df[df["代码"] == sina_code]
            if not row.empty:
                row = row.iloc[0]
                indices.append({
                    "index_code": code,
                    "index_name": name,
                    "close": float(row.get("最新价", 0)),
                    "change_pct": float(row.get("涨跌幅", 0)),
                    "turnover": float(row.get("成交额", 0)),
                })
        return indices
    except Exception as e:
        print(f"[AkShare Index Error] {e}")
        raise


@retry(max_retries=3, delay=2)
def _fetch_sectors() -> list[dict]:
    """获取行业板块行情"""
    try:
        # 使用新浪接口（更稳定）
        df = ak.stock_sector_spot(indicator="行业")

        sectors = []
        for _, row in df.head(10).iterrows():
            sectors.append({
                "sector_name": str(row.get("名称", "")),
                "sector_type": "industry",
                "change_pct": float(row.get("涨跌幅", 0)),
                "turnover": float(row.get("总成交额", 0)),
                "leading_stocks": str(row.get("领涨股票", "")),
            })
        return sectors
    except Exception as e:
        print(f"[AkShare Sector Error] {e}")
        raise


@retry(max_retries=3, delay=2)
def _fetch_stocks() -> list[dict]:
    """获取个股行情"""
    try:
        # 使用新浪接口（更稳定）
        df = ak.stock_zh_a_spot()

        stocks = []
        for _, row in df.iterrows():
            name = str(row.get("名称", ""))
            code = str(row.get("代码", ""))
            close = float(row.get("最新价", 0) or 0)
            change_pct = float(row.get("涨跌幅", 0) or 0)
            turnover = float(row.get("成交额", 0) or 0)
            volume_ratio = float(row.get("量比", 1) or 1)
            market_cap = float(row.get("总市值", 0) or 0)

            # 跳过无效数据
            if close <= 0 or turnover <= 0:
                continue

            stocks.append({
                "code": code,
                "name": name,
                "close": close,
                "change_pct": change_pct,
                "turnover": turnover,
                "volume_ratio": volume_ratio,
                "market_cap": market_cap,
                "industry": str(row.get("所属行业", "")),
                "concept": "",
                "is_st": "ST" in name,
                "is_suspended": False,
                "five_day_change_pct": 0,
                "trend_breakout": False,
            })

        return stocks
    except Exception as e:
        print(f"[AkShare Stock Error] {e}")
        raise
