from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import akshare as ak


# ============================================================================
# 预置种子股票列表 — 断网环境下也能搜索
# ============================================================================

_SEED_STOCKS = [
    # 沪市主板（6 开头）
    ("600519", "贵州茅台", "sh"),
    ("601318", "中国平安", "sh"),
    ("600036", "招商银行", "sh"),
    ("600276", "恒瑞医药", "sh"),
    ("600887", "伊利股份", "sh"),
    ("600030", "中信证券", "sh"),
    ("601012", "隆基绿能", "sh"),
    ("600900", "长江电力", "sh"),
    ("601899", "紫金矿业", "sh"),
    ("600309", "万华化学", "sh"),
    ("601166", "兴业银行", "sh"),
    ("601988", "中国银行", "sh"),
    # 深市主板（0 开头）
    ("000001", "平安银行", "sz"),
    ("000002", "万科A", "sz"),
    ("000858", "五粮液", "sz"),
    ("000333", "美的集团", "sz"),
    ("002415", "海康威视", "sz"),
    ("000651", "格力电器", "sz"),
    ("002594", "比亚迪", "sz"),
    ("000063", "中兴通讯", "sz"),
    ("000725", "京东方A", "sz"),
    # 创业板（3 开头）
    ("300750", "宁德时代", "sz"),
    ("300760", "迈瑞医疗", "sz"),
    ("300059", "东方财富", "sz"),
    ("300751", "迈为股份", "sz"),
    ("300124", "汇川技术", "sz"),
]


@dataclass
class SearchResult:
    code: str
    name: str
    market: str  # 'sh' / 'sz'


def search_stocks(q: str, limit: int = 10) -> tuple[list[SearchResult], int]:
    """
    在 SQLite stock_info 表中搜索股票

    支持：
    - 精确代码搜索：'600519'
    - 名称模糊搜索：'茅台'
    - 回退：数据库为空时，从内置种子列表匹配
    """
    if not q or len(q.strip()) < 1:
        return [], 0

    q = q.strip()

    try:
        from app.storage import MarketStore

        store = MarketStore()
        items = store.search_stock_info(q, limit)
        if items:
            return items, len(items)
    except Exception:
        pass

    # ——— 回退：数据库为空时，从内置种子列表匹配 ———
    from dataclasses import asdict
    lower_q = q.lower()
    matched: list[dict] = []
    for code, name, market in _SEED_STOCKS:
        if lower_q in code.lower() or lower_q in name.lower():
            matched.append(asdict(SearchResult(code=code, name=name, market=market)))
            if len(matched) >= limit:
                break
    return matched, len(matched)


def sync_stock_info() -> int:
    """
    从 AkShare 拉取全市场 A 股代码列表，写入 stock_info 表。

    每日凌晨执行一次，保持股票列表最新。
    返回同步的股票数量。
    """
    try:
        df = ak.stock_info_a_code_name()
        count = 0

        from app.storage import MarketStore

        store = MarketStore()

        for _, row in df.iterrows():
            code = str(row.get("code", "")).strip()
            name = str(row.get("name", "")).strip()
            if not code or not name or len(code) != 6:
                continue
            if code.startswith(("6", "5", "9", "11")):
                market = "sh"
            elif code.startswith(("0", "1", "2", "3")):
                market = "sz"
            else:
                market = "other"
            store.save_stock_info(code, name, market)
            count += 1
        print(f"[Sync] stock_info 同步完成，共 {count} 只股票")
        return count
    except Exception as e:
        # ——— AkShare 失败时，用种子数据兜底 ———
        try:
            from app.storage import MarketStore

            store = MarketStore()
            for code, name, market in _SEED_STOCKS:
                store.save_stock_info(code, name, market)
            print(f"[Sync] AkShare 不可用，用 {len(_SEED_STOCKS)} 只种子股票兜底 ({e})")
            return len(_SEED_STOCKS)
        except Exception as e2:
            print(f"[Sync] 种子数据写入失败: {e2}")
            return 0


def ensure_seed_stocks() -> int:
    """
    确保 stock_info 表中至少有种子股票。
    如果 stock_info 为空，则批量写入种子数据（单事务 executemany）。
    """
    try:
        from app.storage import MarketStore
        store = MarketStore()
        # 检查表中是否已有数据
        codes = store.all_stock_codes()
        if codes and len(codes) > 0:
            return 0
        store.save_stock_info_many(_SEED_STOCKS)
        return len(_SEED_STOCKS)
    except Exception:
        return 0
