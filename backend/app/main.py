from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import DISCLAIMER
from app.data_source import load_market_data
from app.history import fetch_history, HistoryError, _map_akshare_error
from app.reporting import build_daily_report, market_temperature
from app.scheduler import setup_scheduler, shutdown_scheduler
from app.scoring import score_strong_stocks
from app.search import search_stocks, ensure_seed_stocks
from app.storage import MarketStore


def envelope(data, updated_at: str | None, source: str | None) -> dict:
    return {
        "data": data,
        "updated_at": updated_at,
        "source": source or "sample-akshare-compatible",
        "risk_disclaimer": DISCLAIMER,
    }


def refresh_market(store: MarketStore) -> dict:
    payload = load_market_data()
    sector_strength = {item["sector_name"]: item["change_pct"] for item in payload["sectors"]}
    scored_stocks = score_strong_stocks(payload["stocks"], sector_strength)
    report = build_daily_report(payload["indices"], payload["sectors"], scored_stocks)
    updated_at = store.save_snapshot(payload, scored_stocks, report)
    return {
        "status": "ok",
        "date": payload["date"],
        "updated_at": updated_at,
        "source": payload["source"],
    }


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 启动时初始化定时任务
        setup_scheduler(store)
        yield
        # 关闭时清理定时任务
        shutdown_scheduler()

    app = FastAPI(
        title="A股每日行情与强势观察",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://*.vercel.app"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    store = MarketStore(database_url)
    # 确保有种子股票数据（断网环境下也能搜索）
    seed_count = ensure_seed_stocks()
    if seed_count > 0:
        print(f"[Startup] 预置 {seed_count} 只种子股票到 stock_info 表")

    def ensure_data() -> tuple[str | None, str | None]:
        rows, updated_at, source = store.latest("market_snapshot")
        if not rows:
            result = refresh_market(store)
            return result["updated_at"], result.get("source", "akshare")
        return updated_at, source

    @app.get("/api/market/overview")
    def market_overview():
        ensure_data()
        indices, updated_at, source = store.latest("market_snapshot")
        return envelope({"indices": indices, "market_state": market_temperature(indices)}, updated_at, source)

    @app.get("/api/sectors/rank")
    def sector_rank():
        ensure_data()
        sectors, updated_at, source = store.latest("sector_daily")
        return envelope(sectors, updated_at, source)

    @app.get("/api/stocks/strong")
    def strong_stocks():
        ensure_data()
        stocks, updated_at, source = store.latest_stocks()
        return envelope(stocks[:20], updated_at, source)

    @app.get("/api/stocks/risk")
    def risk_stocks():
        ensure_data()
        stocks, updated_at, source = store.latest_stocks()
        risky = [stock for stock in stocks if stock["risk_tags"]]
        return envelope(risky, updated_at, source)

    @app.get("/api/reports/daily")
    def daily_report():
        ensure_data()
        report, updated_at, source = store.latest_report()
        return envelope(report, updated_at, source)

    @app.post("/api/jobs/refresh")
    def refresh_job():
        result = refresh_market(store)
        return envelope(result, result.get("updated_at"), result.get("source", "akshare"))

    @app.get("/api/scheduler/status")
    def scheduler_status():
        from app.scheduler import scheduler
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })
        return {"running": scheduler.running, "jobs": jobs}

    # =======================================================================
    # 个股历史行情 API — 新增
    # =======================================================================

    @app.get("/api/stocks/history")
    def get_stock_history(
        code: str = Query(..., description="6位股票代码，如 600519"),
        period: str = Query("daily", description="周期: daily / weekly / monthly"),
        adjust: str = Query("qfq", description="复权: qfq / none"),
        start: str | None = Query(None, description="起始日期 YYYY-MM-DD，不传则自动计算"),
        end: str | None = Query(None, description="结束日期 YYYY-MM-DD，不传则默认今天"),
    ):
        """
        获取个股历史行情（K线数据）

        - 从 SQLite 缓存读取（命中则秒级响应）
        - 未命中则从 AkShare 拉取并存入缓存
        - 首次冷启动约需 15~45 秒
        """
        try:
            result = fetch_history(
                code=code,
                period=period,   # type: ignore
                adjust=adjust,   # type: ignore
                start=start,
                end=end,
            )
            return envelope(result.to_dict(), datetime.now().isoformat(timespec="seconds"), "akshare")
        except HistoryError as e:
            raise HTTPException(status_code=e.http_status, detail=e.to_dict())

    @app.get("/api/stocks/search")
    def search_stocks_api(
        q: str = Query(..., min_length=1, description="搜索关键词（代码或名称）"),
        limit: int = Query(10, ge=1, le=50, description="返回条数上限"),
    ):
        """股票代码/名称模糊搜索"""
        items, total = search_stocks(q=q, limit=limit)
        return envelope(
            {"items": items, "total": total},
            datetime.now().isoformat(timespec="seconds"),
            "akshare",
        )

    return app


app = create_app()
