from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import require_valid_api_key
from app.db.database import get_session
from app.tools.tracker import EmailBox, JobTracker

router = APIRouter(prefix="/api/stats", tags=["stats"], dependencies=[Depends(require_valid_api_key)])


class DashboardStats(BaseModel):
    total_applied: int
    awaiting_reply: int
    under_review: int
    interview: int
    declined: int
    accepted: int
    no_response: int
    emails_seen: int
    emails_unread: int
    emails_replied: int
    reply_rate: float


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(session: AsyncSession = Depends(get_session)) -> DashboardStats:
    job_tracker = JobTracker(session)
    email_box = EmailBox(session)
    counts = await job_tracker.job_status_counts()
    replies = await email_box.list_emails(limit=10000)
    total_applied = sum(counts.values())
    replied_or_further = counts["under_review"] + counts["interview"] + counts["accepted"]
    reply_rate = (replied_or_further / total_applied * 100) if total_applied else 0.0
    return DashboardStats(
        total_applied=total_applied,
        awaiting_reply=counts["applied"],
        under_review=counts["under_review"],
        interview=counts["interview"],
        declined=counts["declined"],
        accepted=counts["accepted"],
        no_response=counts["no_response"],
        emails_seen=len(replies),
        emails_unread=sum(1 for email in replies if not email.is_read),
        emails_replied=sum(1 for email in replies if email.is_replied),
        reply_rate=round(reply_rate, 1),
    )