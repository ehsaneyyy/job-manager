import httpx

from app.core.config import settings


async def send_push_notification(title: str, body: str, topic: str | None = None) -> None:
    active_topic = topic or "jobmanager-updates"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://ntfy.sh/{active_topic}",
                content=body,
                headers={
                    "Title": title,
                    "Priority": "default",
                },
            )
    except Exception:
        return


def notify_job_status(job_summary: str, status: str) -> None:
    import asyncio

    asyncio.create_task(send_push_notification(f"Job update: {status}", job_summary))


async def notify_daily_summary(summary_text: str) -> None:
    await send_push_notification("Daily job search summary", summary_text)