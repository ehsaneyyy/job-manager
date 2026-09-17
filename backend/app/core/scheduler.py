import asyncio
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.db.database import async_session_factory
from app.tools.notifier import send_push_notification
from app.tools.tracker import JobTracker

logger = logging.getLogger("jobmanager.scheduler")

follow_up_check_interval_seconds = 3600


async def run_follow_up_reminders() -> None:
    async with async_session_factory() as session:
        tracker = JobTracker(session)
        due_jobs = await tracker.jobs_due_for_follow_up()
        if not due_jobs:
            return
        lines = [f"- {job.company} — {job.role} (status: {job.status})" for job in due_jobs]
        await send_push_notification(
            title="Follow-up reminders",
            body="Jobs waiting for you to check:\n" + "\n".join(lines),
        )


async def run_daily_summary() -> None:
    summary_file = settings.data_dir / "last_daily_summary"
    today = date.today().isoformat()
    if summary_file.exists() and summary_file.read_text(encoding="utf-8").strip() == today:
        return
    async with async_session_factory() as session:
        tracker = JobTracker(session)
        counts = await tracker.job_status_counts()
    total = sum(counts.values())
    summary = (
        f"Today's summary: {total} total applications.\n"
        + "\n".join(f"{status}: {count}" for status, count in counts.items())
    )
    await send_push_notification(title="Daily job search summary", body=summary)
    summary_file.write_text(today, encoding="utf-8")


async def scheduler_loop() -> None:
    logger.info("Scheduler started")
    while True:
        try:
            await run_follow_up_reminders()
            await run_daily_summary()
        except Exception as exc:
            logger.warning("Scheduler tick failed: %s", exc)
        await asyncio.sleep(follow_up_check_interval_seconds)