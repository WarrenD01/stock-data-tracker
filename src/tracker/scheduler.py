from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from tracker.emailer import send_morning_report
from tracker.prices import record_close_snapshot

logger = logging.getLogger(__name__)
ET = ZoneInfo("America/New_York")


def _snapshot_job() -> None:
    try:
        recorded = record_close_snapshot(force=False)
        logger.info("Market-close snapshot completed (%d tickers updated).", len(recorded))
    except Exception:
        logger.exception("Market-close snapshot job failed.")


def _email_job() -> None:
    try:
        sent = send_morning_report()
        logger.info("Morning report job finished (sent=%s).", sent)
    except Exception:
        logger.exception("Morning report job failed.")


def run_scheduler() -> None:
    """Start the blocking scheduler in US/Eastern time until interrupted."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    scheduler = BlockingScheduler(timezone=ET)

    # 4:05 PM ET market-close snapshot (Mon-Fri)
    scheduler.add_job(
        _snapshot_job,
        CronTrigger(day_of_week="mon-fri", hour=16, minute=5, timezone=ET),
        id="market_close_snapshot",
        name="Pull daily market-close prices at 4:05 PM ET",
        replace_existing=True,
    )

    # 8:00 AM ET morning email report
    scheduler.add_job(
        _email_job,
        CronTrigger(hour=8, minute=0, timezone=ET),
        id="morning_email_report",
        name="Send 8:00 AM ET stock performance email",
        replace_existing=True,
    )

    logger.info("Scheduler started (ET timezone). Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")