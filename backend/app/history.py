from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from enum import Enum
from typing import Literal, Optional

import pandas as pd


# ============================================================================
# 类型别名
# ============================================================================

Period = Literal["daily", "weekly", "monthly"]
Adjust = Literal["qfq", "none"]


# ============================================================================
# 错误枚举
# ============================================================================

class HistoryErrorCode(Enum):
    INVALID_CODE = ("INVALID_CODE", 400, "股票代码格式错误，应为6位数字")
    STOCK_NOT_FOUND = ("STOCK_NOT_FOUND", 404, "未找到该股票，可能代码错误或已退市")
    FETCH_TIMEOUT = ("FETCH_TIMEOUT", 408, "数据源请求超时，请稍后重试")
    RATE_LIMITED = ("RATE_LIMITED", 429, "请求过于频繁，请30秒后再试")
    SOURCE_UNAVAILABLE = (
        "SOURCE_UNAVAILABLE",
        503,
        "数据源暂时不可用，请稍后重试；首次冷启动需联网拉取历史数据",
    )
    INTERNAL_ERROR = ("INTERNAL_ERROR", 500, "服务器内部错误")


class HistoryError(Exception):
    def __init__(self, code: HistoryErrorCode):
        self.code = code
        self.http_status = code.value[1]
        self.message = code.value[2]

    def to_dict(self) -> dict:
        return {"code": self.code.value[0], "message": self.message}


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class HistoryResult:
    code: str
    name: str
    period: Period
    adjust: Adjust
    start_date: str
    end_date: str
    total_count: int
    latest_close: float
    latest_change_pct: float
    candles: list[dict]
    source: str = "akshare"

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================================
# 全局锁 — 防止 AkShare 并发触发限频
# ============================================================================

_akshare_lock = threading.Lock()


# ============================================================================
# 工具函数
# ============================================================================

def _date_range(period: Period) -> tuple[str, str]:
    """根据周期自动计算回溯起始日期"""
    today = date.today()
    end = today.isoformat()
    if period == "daily":
        start = (today - timedelta(days=365 * 3)).isoformat()
    elif period == "weekly":
        start = (today - timedelta(days=365 * 5)).isoformat()
    else:  # monthly
        start = (today - timedelta(days=365 * 10)).isoformat()
    return start, end


def _validate_code(code: str) -> str:
    """校验并规范化股票代码"""
    code = code.strip()
    if not (code.isdigit() and len(code) == 6):
        raise HistoryError(HistoryErrorCode.INVALID_CODE)
    return code


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """将 AkShare 返回的 DataFrame 列名标准化"""
    column_map = {
        "日期": "trade_date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover",
    }
    available = {k: v for k, v in column_map.items() if k in df.columns}
    return df.rename(columns=available)


def _market_prefix(code: str) -> str:
    """根据代码判断市场前缀（sh/sz）"""
    if code.startswith(("6", "5", "9", "11")):
        return "sh"
    return "sz"


# ============================================================================
# AkShare 数据拉取
# ============================================================================

@staticmethod
def _fetch_from_akshare(code: str, period: Period, adjust: Adjust, start: str, end: str) -> pd.DataFrame:
    """从 AkShare 拉取原始历史数据（延迟导入，避免模块加载时阻塞）"""
    import akshare as ak

    # 去掉横杠，AkShare 接口用 YYYYMMDD 格式
    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")

    adjust_map: dict[Adjust, str] = {"qfq": "qfq", "none": ""}

    # stock_zh_a_hist 支持 period= daily/weekly/monthly, adjust= qfq/qfq/none
    df = ak.stock_zh_a_hist(
        symbol=code,
        start_date=start_fmt,
        end_date=end_fmt,
        period=period,
        adjust=adjust_map[adjust],
    )
    return _normalize_columns(df)


# ============================================================================
# 主入口
# ============================================================================

def fetch_history(
    code: str,
    period: Period = "daily",
    adjust: Adjust = "qfq",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> HistoryResult:
    """
    从缓存或 AkShare 获取个股历史数据

    策略：
    1. 校验 code 格式
    2. 计算日期范围
    3. 查 SQLite 缓存（命中则直接返回）
    4. 未命中则加全局锁调 AkShare，存入缓存后返回
    """
    code = _validate_code(code)

    if start is None or end is None:
        start, end = _date_range(period)

    # 尝试从缓存读取
    cached = _read_from_cache(code, period, adjust, start, end)
    if cached is not None:
        return cached

    # 加全局锁，防止并发触发 AkShare 限频
    with _akshare_lock:
        try:
            df = _fetch_from_akshare(code, period, adjust, start, end)
        except Exception as e:
            err_lower = str(e).lower()
            if "not found" in err_lower or "不存在" in err_lower or "error" in err_lower:
                # 尝试用 symbol 参数兼容旧版 AkShare
                try:
                    df = _fetch_by_symbol_compat(code, period, adjust, start, end)
                except Exception:
                    # ——— 降级 1：从 stock_daily 本地表构造简化 K 线 ———
                    fallback = _fallback_from_stock_daily(code, period, start, end)
                    if fallback is not None:
                        return fallback
                    # ——— 降级 2：从 mock 种子股票生成确定性 K 线 ———
                    mock = _mock_seed_candles(code, period, start, end)
                    if mock is not None:
                        return mock
                    raise _map_akshare_error(e)
            else:
                fallback = _fallback_from_stock_daily(code, period, start, end)
                if fallback is not None:
                    return fallback
                mock = _mock_seed_candles(code, period, start, end)
                if mock is not None:
                    return mock
                raise _map_akshare_error(e)

    if df is None or df.empty:
        raise HistoryError(HistoryErrorCode.STOCK_NOT_FOUND)

    # 转换为结果对象
    latest = df.iloc[-1]
    name = _get_stock_name_from_info(code)

    # 提取 K 线数据
    candle_cols = ["trade_date", "open", "high", "low", "close", "volume"]
    available_cols = [c for c in candle_cols if c in df.columns]
    candles = df[available_cols].to_dict(orient="records")

    # 转换数值类型
    for c in candles:
        for key in ["open", "high", "low", "close"]:
            if key in c:
                c[key] = float(c[key])
        if "volume" in c:
            c["volume"] = int(c["volume"])

    # 计算涨跌幅（如果有的话）
    change_pct = 0.0
    if len(df) >= 2:
        prev_close = float(df.iloc[-2]["close"])
        curr_close = float(df.iloc[-1]["close"])
        if prev_close > 0:
            change_pct = round((curr_close - prev_close) / prev_close * 100, 2)

    result = HistoryResult(
        code=code,
        name=name or code,
        period=period,
        adjust=adjust,
        start_date=start,
        end_date=end,
        total_count=len(candles),
        latest_close=float(latest["close"]),
        latest_change_pct=change_pct,
        candles=candles,
    )

    # 存入缓存
    _save_to_cache(result)

    return result


def _fetch_by_symbol_compat(
    code: str, period: Period, adjust: Adjust, start: str, end: str
) -> pd.DataFrame:
    """兼容旧版 AkShare 的 symbol 参数写法（延迟导入）"""
    import akshare as ak

    start_fmt = start.replace("-", "")
    end_fmt = end.replace("-", "")
    prefix = _market_prefix(code)
    symbol = f"{prefix}{code}"
    adjust_map: dict[Adjust, str] = {"qfq": "qfq", "none": ""}
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        start_date=start_fmt,
        end_date=end_fmt,
        period=period,
        adjust=adjust_map[adjust],
    )
    return _normalize_columns(df)


def _map_akshare_error(e: Exception) -> HistoryError:
    """将 AkShare 异常映射为 HistoryError"""
    err_str = str(e).lower()
    # ——— 明确的网络错误 ———
    if any(k in err_str for k in [
        "proxy", "connection", "disconnected", "maxretry",
        "network", "unreachable", "resolve", "dns", "refused",
        "timeout", "超时",
    ]):
        return HistoryError(HistoryErrorCode.SOURCE_UNAVAILABLE)
    # ——— 明确的 404 / 股票不存在 ———
    if "not found" in err_str or "不存在" in err_str or "404" in err_str:
        return HistoryError(HistoryErrorCode.STOCK_NOT_FOUND)
    # ——— 被限频 ———
    if "429" in err_str or "rate" in err_str or "频繁" in err_str:
        return HistoryError(HistoryErrorCode.RATE_LIMITED)
    return HistoryError(HistoryErrorCode.INTERNAL_ERROR)


# ============================================================================
# 缓存读写（依赖 storage.py 的 MarketStore）
# ============================================================================

def _read_from_cache(
    code: str, period: Period, adjust: Adjust, start: str, end: str
) -> Optional[HistoryResult]:
    """从 SQLite 读取缓存，有数据则返回 HistoryResult"""
    try:
        from app.storage import MarketStore

        store = MarketStore()
        rows = store.read_history(code, period, adjust, start, end)
        if not rows:
            return None

        # 取 stock_name（如果有的话）
        name = _get_stock_name_from_info(code) or code

        first_row = rows[0]
        latest_row = rows[-1]

        return HistoryResult(
            code=code,
            name=name,
            period=period,
            adjust=adjust,
            start_date=start,
            end_date=end,
            total_count=len(rows),
            latest_close=float(latest_row.get("close", 0)),
            latest_change_pct=float(latest_row.get("change_pct", 0)),
            candles=rows,
        )
    except Exception:
        return None


def _save_to_cache(result: HistoryResult) -> None:
    """将历史数据写入 SQLite 缓存"""
    try:
        from app.storage import MarketStore

        store = MarketStore()
        store.save_history(result.code, result.period, result.adjust, result.candles)
    except Exception:
        pass  # 缓存写入失败不影响主流程


# ============================================================================
# 缓存预热（供 scheduler 调用）
# ============================================================================

def refresh_history_cache(period: Period = "daily") -> None:
    """
    从 stock_info 表读取全市场股票列表，逐只追加今日历史数据。
    每次只追加当天一根新 K 线，数据量小，不会触发 AkShare 限频。
    """
    try:
        from app.storage import MarketStore

        store = MarketStore()
        stock_list = store.all_stock_codes()

        today = date.today().isoformat()

        for code, stock_name in stock_list:
            try:
                # 只拉今天一天的数据（量小，速度快）
                rows = _fetch_from_akshare(code, period, "qfq", today, today)
                if not rows.empty:
                    candles = rows[["trade_date", "open", "high", "low", "close", "volume"]].to_dict(
                        orient="records"
                    )
                    for c in candles:
                        for key in ["open", "high", "low", "close"]:
                            c[key] = float(c[key])
                        c["volume"] = int(c["volume"])
                    store.save_history(code, period, "qfq", candles)
                    print(f"[Cache] {code} {period} 缓存更新成功")
            except Exception as e:
                print(f"[Cache] {code} 更新失败: {e}")
                time.sleep(1)  # 单只失败后稍作停顿，避免雪崩

    except Exception as e:
        print(f"[Cache] refresh_history_cache 执行失败: {e}")


def _get_stock_name_from_info(code: str) -> Optional[str]:
    """从 stock_info 表查询股票名称"""
    try:
        from app.storage import MarketStore

        store = MarketStore()
        name = store.get_stock_name(code)
        return name
    except Exception:
        return None


# ============================================================================
# 降级策略：AkShare 不可用时从 stock_daily 构造简化 K 线
# ============================================================================

def _fallback_from_stock_daily(
    code: str, period: Period, start: str, end: str
) -> Optional[HistoryResult]:
    """
    当 AkShare 数据源不可用时，从本地 stock_daily 表组装简化 K 线。

    适用场景：
    - 开发/测试环境断网
    - AkShare 临时故障
    - 冷启动尚未拉取全量数据

    返回 None 表示无可用降级数据。
    """
    try:
        import sqlite3
        from app.config import DEFAULT_DB_PATH

        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # stock_daily 表中的 code 可能带 sh/sz 前缀，也可能是纯数字
        prefix = _market_prefix(code)
        code_patterns = [code, f"{prefix}{code}"]

        rows = []
        for cp in code_patterns:
            rows = cur.execute(
                """
                SELECT date, close, change_pct, volume_ratio, turnover
                  FROM stock_daily
                 WHERE code = ?
                   AND date >= ?
                   AND date <= ?
                 ORDER BY date ASC
                """,
                (cp, start, end),
            ).fetchall()
            if rows:
                break
        conn.close()

        if not rows:
            return None

        # 由于 stock_daily 只有收盘价，我们需要构造 OHLC。
        # 策略：用 change_pct 反推前一日 close 作为 open，
        # high = close * (1 + |change_pct|/2 + 0.003),
        # low  = close * (1 - |change_pct|/2 - 0.002)
        # 这是粗略的近似值，用于"数据源不可用"场景下的降级展示。
        candles: list[dict] = []
        closes: list[float] = []

        for i, row in enumerate(rows):
            close = float(row["close"])
            change_pct = float(row["change_pct"])
            trade_date = row["date"]

            # 用当日收盘价 + 当日涨跌幅反推"开盘价"
            if close > 0 and change_pct != 0:
                prev_estimate = close / (1 + change_pct / 100)
            else:
                prev_estimate = close * 0.999

            open_price = round(prev_estimate, 2)
            spread = abs(change_pct) / 100 * close + close * 0.005
            high = round(close + spread * 0.6, 2)
            low = round(close - spread * 0.6, 2)
            volume = int(float(row["volume_ratio"] or 1) * 1_000_000)

            candles.append({
                "trade_date": trade_date,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            })
            closes.append(close)

        latest_close = closes[-1]
        latest_change_pct = float(rows[-1]["change_pct"])

        name = _get_stock_name_from_info(code) or code

        return HistoryResult(
            code=code,
            name=name,
            period=period,
            adjust="qfq",
            start_date=start,
            end_date=end,
            total_count=len(candles),
            latest_close=latest_close,
            latest_change_pct=latest_change_pct,
            candles=candles,
            source="local_fallback",
        )
    except Exception:
        return None


# ============================================================================
# 终极降级：对种子股票生成确定性 mock K 线（完全断网 + 无本地数据）
# ============================================================================

# 种子股票的基准价格（用于 mock 数据）
_SEED_BASE_PRICES: dict[str, tuple[str, float]] = {
    "600519": ("贵州茅台", 1780.00),
    "601318": ("中国平安", 52.00),
    "600036": ("招商银行", 38.00),
    "600276": ("恒瑞医药", 48.00),
    "600887": ("伊利股份", 28.00),
    "000001": ("平安银行", 12.00),
    "000002": ("万科A", 8.50),
    "000858": ("五粮液", 155.00),
    "000333": ("美的集团", 72.00),
    "002415": ("海康威视", 32.00),
    "002594": ("比亚迪", 260.00),
    "300750": ("宁德时代", 220.00),
    "300760": ("迈瑞医疗", 240.00),
    "300059": ("东方财富", 14.50),
}


def _mock_seed_candles(code: str, period: Period, start: str, end: str) -> Optional[HistoryResult]:
    """对已知种子股票生成确定性 mock K 线（完全断网场景）"""
    if code not in _SEED_BASE_PRICES:
        return None

    try:
        from datetime import datetime, timedelta as td

        name, base_price = _SEED_BASE_PRICES[code]

        start_dt = datetime.strptime(start, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end, "%Y-%m-%d").date()

        # 根据周期决定步长
        if period == "daily":
            step = td(days=1)
        elif period == "weekly":
            step = td(days=7)
        else:
            step = td(days=30)

        # 用 code 作为随机种子，保证每次同样请求返回同样数据
        import hashlib

        seed = int(hashlib.md5(f"{code}_{period}".encode()).hexdigest()[:8], 16)
        rng = _deterministic_rng(seed)

        candles: list[dict] = []
        price = base_price
        current = start_dt

        while current <= end_dt:
            # 跳过周末（日线）
            if period == "daily" and current.weekday() >= 5:
                current += step
                continue

            # 确定性波动：涨跌幅在 -2% 到 +2.5% 之间
            change = (rng() - 0.45) * 0.05  # -0.0225 ~ 0.0275
            close = round(price * (1 + change), 2)
            open_price = round(price * (1 + (rng() - 0.5) * 0.01), 2)
            high = round(max(open_price, close) * (1 + rng() * 0.008), 2)
            low = round(min(open_price, close) * (1 - rng() * 0.008), 2)
            volume = int(1_000_000 + rng() * 5_000_000)

            candles.append({
                "trade_date": current.isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            })

            price = close
            current += step

        if not candles:
            return None

        last_close = candles[-1]["close"]
        last_open = candles[-1]["open"]
        latest_change_pct = round((last_close - last_open) / last_open * 100, 2)

        return HistoryResult(
            code=code,
            name=name,
            period=period,
            adjust="qfq",
            start_date=start,
            end_date=end,
            total_count=len(candles),
            latest_close=last_close,
            latest_change_pct=latest_change_pct,
            candles=candles,
            source="mock_seed",
        )
    except Exception:
        return None


def _deterministic_rng(seed: int):
    """简单的确定性伪随机数生成器"""
    state = seed % (2**31 - 1)

    def rng():
        nonlocal state
        state = (state * 1103515245 + 12345) % (2**31 - 1)
        return state / (2**31 - 1)

    return rng
