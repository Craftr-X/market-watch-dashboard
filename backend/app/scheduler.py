from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.storage import MarketStore


scheduler = BackgroundScheduler()


def setup_scheduler(store: MarketStore) -> None:
    """配置定时任务"""
    from app.main import refresh_market

    # 每个交易日 15:30 自动刷新（周一到周五）
    scheduler.add_job(
        refresh_market,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=15,
            minute=30,
            timezone="Asia/Shanghai",
        ),
        args=[store],
        id="daily_refresh",
        name="每日行情刷新",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] 定时任务已启动，每个交易日 15:30 自动刷新")


def shutdown_scheduler() -> None:
    """关闭定时任务"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] 定时任务已关闭")
