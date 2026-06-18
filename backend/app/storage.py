from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from app.config import DEFAULT_DB_PATH


def database_path(database_url: str | None = None) -> Path:
    if not database_url:
        return DEFAULT_DB_PATH
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Only sqlite database URLs are supported")
    return Path(parsed.path)


class MarketStore:
    def __init__(self, database_url: str | None = None):
        self.path = database_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                -- === 现有表（保持不变）===
                CREATE TABLE IF NOT EXISTS market_snapshot (
                    date TEXT NOT NULL,
                    index_code TEXT NOT NULL,
                    index_name TEXT NOT NULL,
                    close REAL NOT NULL,
                    change_pct REAL NOT NULL,
                    turnover REAL NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (date, index_code)
                );
                CREATE TABLE IF NOT EXISTS stock_daily (
                    date TEXT NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    close REAL NOT NULL,
                    change_pct REAL NOT NULL,
                    turnover REAL NOT NULL,
                    volume_ratio REAL NOT NULL,
                    market_cap REAL NOT NULL,
                    industry TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    is_st INTEGER NOT NULL,
                    is_suspended INTEGER NOT NULL,
                    five_day_change_pct REAL NOT NULL,
                    trend_breakout INTEGER NOT NULL,
                    score REAL NOT NULL,
                    strength_reason TEXT NOT NULL,
                    risk_tags TEXT NOT NULL,
                    risk_note TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (date, code)
                );
                CREATE TABLE IF NOT EXISTS sector_daily (
                    date TEXT NOT NULL,
                    sector_name TEXT NOT NULL,
                    sector_type TEXT NOT NULL,
                    change_pct REAL NOT NULL,
                    turnover REAL NOT NULL,
                    leading_stocks TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (date, sector_name, sector_type)
                );
                CREATE TABLE IF NOT EXISTS daily_report (
                    date TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    strong_sectors TEXT NOT NULL,
                    strong_stocks TEXT NOT NULL,
                    risk_notes TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL
                );

                -- === 新增：个股历史行情表 ===
                CREATE TABLE IF NOT EXISTS stock_history (
                    code        TEXT    NOT NULL,
                    period      TEXT    NOT NULL,
                    adjust      TEXT    NOT NULL,
                    trade_date  TEXT    NOT NULL,
                    open        REAL    NOT NULL,
                    high        REAL    NOT NULL,
                    low         REAL    NOT NULL,
                    close       REAL    NOT NULL,
                    volume      INTEGER NOT NULL,
                    amount      REAL    NOT NULL,
                    turnover    REAL    NOT NULL,
                    updated_at  TEXT    NOT NULL,
                    source      TEXT    NOT NULL DEFAULT 'akshare',
                    PRIMARY KEY (code, period, adjust, trade_date)
                );
                CREATE INDEX IF NOT EXISTS idx_history_lookup
                    ON stock_history(code, period, adjust, trade_date DESC);

                -- === 新增：股票基础信息表（用于搜索）===
                CREATE TABLE IF NOT EXISTS stock_info (
                    code        TEXT    PRIMARY KEY,
                    name        TEXT    NOT NULL,
                    market      TEXT    NOT NULL,
                    list_date   TEXT    NOT NULL DEFAULT '2000-01-01',
                    updated_at  TEXT    NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_info_name ON stock_info(name);
                """
            )

    def save_snapshot(self, payload: dict, scored_stocks: list[dict], report: dict) -> str:
        updated_at = datetime.now().isoformat(timespec="seconds")
        day = payload["date"]
        source = payload["source"]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO market_snapshot
                VALUES (:date, :index_code, :index_name, :close, :change_pct, :turnover, :updated_at, :source)
                """,
                [{**item, "date": day, "updated_at": updated_at, "source": source} for item in payload["indices"]],
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO sector_daily
                VALUES (:date, :sector_name, :sector_type, :change_pct, :turnover, :leading_stocks, :updated_at, :source)
                """,
                [{**item, "date": day, "updated_at": updated_at, "source": source} for item in payload["sectors"]],
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO stock_daily
                VALUES (
                    :date, :code, :name, :close, :change_pct, :turnover, :volume_ratio, :market_cap,
                    :industry, :concept, :is_st, :is_suspended, :five_day_change_pct, :trend_breakout,
                    :score, :strength_reason, :risk_tags, :risk_note, :updated_at, :source
                )
                """,
                [
                    {
                        **item,
                        "date": day,
                        "is_st": int(bool(item["is_st"])),
                        "is_suspended": int(bool(item["is_suspended"])),
                        "trend_breakout": int(bool(item["trend_breakout"])),
                        "risk_tags": json.dumps(item["risk_tags"], ensure_ascii=False),
                        "updated_at": updated_at,
                        "source": source,
                    }
                    for item in scored_stocks
                ],
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO daily_report
                VALUES (:date, :summary, :strong_sectors, :strong_stocks, :risk_notes, :updated_at, :source)
                """,
                {
                    "date": day,
                    "summary": report["summary"],
                    "strong_sectors": json.dumps(report["strong_sectors"], ensure_ascii=False),
                    "strong_stocks": json.dumps(report["strong_stocks"], ensure_ascii=False),
                    "risk_notes": json.dumps(report["risk_notes"], ensure_ascii=False),
                    "updated_at": updated_at,
                    "source": source,
                },
            )
        return updated_at

    def latest(self, table: str) -> tuple[list[dict], str | None, str | None]:
        with self.connect() as conn:
            date_row = conn.execute(f"SELECT date FROM {table} ORDER BY date DESC LIMIT 1").fetchone()
            if not date_row:
                return [], None, None
            rows = conn.execute(f"SELECT * FROM {table} WHERE date = ? ORDER BY change_pct DESC", (date_row["date"],)).fetchall()
            updated_at = rows[0]["updated_at"] if rows else None
            source = rows[0]["source"] if rows else None
            return [dict(row) for row in rows], updated_at, source

    def latest_stocks(self) -> tuple[list[dict], str | None, str | None]:
        rows, updated_at, source = self.latest("stock_daily")
        for row in rows:
            row["is_st"] = bool(row["is_st"])
            row["is_suspended"] = bool(row["is_suspended"])
            row["trend_breakout"] = bool(row["trend_breakout"])
            row["risk_tags"] = json.loads(row["risk_tags"])
        return sorted(rows, key=lambda item: item["score"], reverse=True), updated_at, source

    def latest_report(self) -> tuple[dict | None, str | None, str | None]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM daily_report ORDER BY date DESC LIMIT 1").fetchone()
        if not row:
            return None, None, None
        report = dict(row)
        report["strong_sectors"] = json.loads(report["strong_sectors"])
        report["strong_stocks"] = json.loads(report["strong_stocks"])
        report["risk_notes"] = json.loads(report["risk_notes"])
        return report, report["updated_at"], report["source"]

    # =======================================================================
    # 个股历史行情 — 新增方法
    # =======================================================================

    def save_history(
        self,
        code: str,
        period: str,
        adjust: str,
        candles: list[dict],
    ) -> None:
        """
        将 K 线数据批量写入 stock_history 表。

        candles 中的每条记录应为：
        { trade_date, open, high, low, close, volume }
        """
        if not candles:
            return

        updated_at = datetime.now().isoformat(timespec="seconds")
        source = "akshare"

        rows = []
        for c in candles:
            rows.append(
                {
                    "code": code,
                    "period": period,
                    "adjust": adjust,
                    "trade_date": str(c.get("trade_date", "")),
                    "open": float(c.get("open", 0)),
                    "high": float(c.get("high", 0)),
                    "low": float(c.get("low", 0)),
                    "close": float(c.get("close", 0)),
                    "volume": int(c.get("volume", 0)),
                    "amount": float(c.get("amount", 0)),
                    "turnover": float(c.get("turnover", 0)),
                    "updated_at": updated_at,
                    "source": source,
                }
            )

        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO stock_history
                (code, period, adjust, trade_date, open, high, low, close, volume, amount, turnover, updated_at, source)
                VALUES
                (:code, :period, :adjust, :trade_date, :open, :high, :low, :close, :volume, :amount, :turnover, :updated_at, :source)
                """,
                rows,
            )

    def read_history(
        self,
        code: str,
        period: str,
        adjust: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """按时间范围读取个股历史行情"""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT trade_date, open, high, low, close, volume, amount, turnover
                FROM stock_history
                WHERE code = ?
                  AND period = ?
                  AND adjust = ?
                  AND trade_date >= ?
                  AND trade_date <= ?
                ORDER BY trade_date ASC
                """,
                (code, period, adjust, start_date, end_date),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_stock_name(self, code: str) -> str | None:
        """从 stock_info 表查询股票名称"""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT name FROM stock_info WHERE code = ?", (code,)
            ).fetchone()
        return row["name"] if row else None

    def all_stock_codes(self) -> list[tuple[str, str]]:
        """返回全市场股票代码列表 [(code, name), ...]"""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT code, name FROM stock_info ORDER BY code"
            ).fetchall()
        return [(r["code"], r["name"]) for r in rows]

    def top_stock_codes(self, limit: int = 50) -> list[tuple[str, str]]:
        """返回按最近评分排序的 Top N 股票 [(code, name), ...]，用于缓存预热"""
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT si.code, si.name
                FROM stock_info si
                INNER JOIN (
                    SELECT code, MAX(score) AS max_score
                    FROM stock_daily
                    GROUP BY code
                    ORDER BY max_score DESC
                    LIMIT ?
                ) sd ON si.code = sd.code
                ORDER BY sd.max_score DESC
                """,
                (limit,),
            ).fetchall()
        # 如果 stock_daily 表为空（冷启动），fallback 到 stock_info 前 N 条
        if not rows:
            with self.connect() as conn:
                rows = conn.execute(
                    "SELECT code, name FROM stock_info ORDER BY code LIMIT ?",
                    (limit,),
                ).fetchall()
        return [(r["code"], r["name"]) for r in rows]

    # =======================================================================
    # 股票基础信息 — 新增方法
    # =======================================================================

    def save_stock_info(self, code: str, name: str, market: str) -> None:
        """写入或更新单条股票基础信息"""
        updated_at = datetime.now().isoformat(timespec="seconds")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO stock_info (code, name, market, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (code, name, market, updated_at),
            )

    def save_stock_info_many(self, rows: list[tuple[str, str, str]]) -> None:
        """
        批量写入股票基础信息（INSERT OR IGNORE，已存在的不覆盖）。
        rows: [(code, name, market), ...]，单事务 executemany。
        """
        if not rows:
            return
        updated_at = datetime.now().isoformat(timespec="seconds")
        payload = [(code, name, market, updated_at) for code, name, market in rows]
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO stock_info (code, name, market, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                payload,
            )

    def search_stock_info(self, q: str, limit: int = 10) -> list[dict]:
        """
        模糊搜索股票代码或名称。
        支持精确代码匹配和名称模糊匹配。
        """
        q_stripped = q.strip()

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT code, name, market
                FROM stock_info
                WHERE
                    code = ?
                    OR code LIKE ?
                    OR name LIKE ?
                    OR name LIKE ?
                ORDER BY
                    CASE WHEN code = ? THEN 0 ELSE 1 END,
                    CASE WHEN code LIKE ? THEN 0 ELSE 1 END,
                    name ASC
                LIMIT ?
                """,
                (
                    q_stripped,
                    f"%{q_stripped}%",
                    f"%{q_stripped}%",
                    f"%{q_stripped}%",
                    q_stripped,
                    f"{q_stripped}%",
                    limit,
                ),
            ).fetchall()
        return [dict(row) for row in rows]
