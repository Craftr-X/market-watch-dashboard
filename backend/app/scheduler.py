from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.storage import MarketStore


scheduler = BackgroundScheduler()


def setup_scheduler(store: MarketStore) -> None:
    """配置定时任务"""
    from app.main import refresh_market

    # === 现有任务：每个交易日 15:30 自动刷新快照 ===
    scheduler.add_job(
        refresh_market,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=15,
            minute=30,
            timezone="Asia/Shanghai",
        ),
        args=[store],
        id="daily_snapshot_refresh",
        name="每日行情快照刷新",
        replace_existing=True,
    )

    # === 新增：每周一 16:00 预热周线缓存 ===
    scheduler.add_job(
        _refresh_weekly_cache,
        trigger=CronTrigger(
            day_of_week="mon",
            hour=16,
            minute=0,
            timezone="Asia/Shanghai",
        ),
        id="weekly_history_cache_refresh",
        name="周线缓存预热（每周一）",
        replace_existing=True,
    )

    # === 新增：每月最后一天 16:30 预热月线缓存 ===
    scheduler.add_job(
        _refresh_monthly_cache,
        trigger=CronTrigger(
            day="last",
            hour=16,
            minute=30,
            timezone="Asia/Shanghai",
        ),
        id="monthly_history_cache_refresh",
        name="月线缓存预热（每月末）",
        replace_existing=True,
    )

    # === 新增：每日凌晨 03:00 同步全市场股票列表 ===
    scheduler.add_job(
        _sync_stock_info,
        trigger=CronTrigger(
            hour=3,
            minute=0,
            timezone="Asia/Shanghai",
        ),
        id="daily_stock_info_sync",
        name="全市场股票列表同步（每日凌晨）",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] 定时任务已启动：每日快照(15:30) / 周线预热(周一16:00) / 月线预热(月末16:30) / 股票列表同步(03:00)")


def _refresh_weekly_cache() -> None:
    """周线缓存预热 — 供定时任务调用"""
    try:
        from app.history import refresh_history_cache
        print("[Scheduler] 开始预热周线缓存...")
        refresh_history_cache(period="weekly")
    except Exception as e:
        print(f"[Scheduler] 周线缓存预热失败: {e}")


def _refresh_monthly_cache() -> None:
    """月线缓存预热 — 供定时任务调用"""
    try:
        from app.history import refresh_history_cache
        print("[Scheduler] 开始预热月线缓存...")
        refresh_history_cache(period="monthly")
    except Exception as e:
        print(f"[Scheduler] 月线缓存预热失败: {e}")


def _sync_stock_info() -> None:
    """全市场股票列表同步 — 供定时任务调用"""
    try:
        from app.search import sync_stock_info
        print("[Scheduler] 开始同步全市场股票列表...")
        count = sync_stock_info()
        print(f"[Scheduler] 股票列表同步完成，共 {count} 只")
    except Exception as e:
        print(f"[Scheduler] 股票列表同步失败: {e}")


def shutdown_scheduler() -> None:
    """关闭定时任务"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] 定时任务已关闭")
