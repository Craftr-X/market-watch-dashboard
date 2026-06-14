from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from backend.app.config import DEFAULT_DB_PATH


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
