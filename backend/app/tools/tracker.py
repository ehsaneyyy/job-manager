from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import ChatMessage, EmailRecord, Job, ProfileEntry, utc_now

VALID_JOB_STATUSES = {"applied", "under_review", "interview", "declined", "accepted", "no_response"}


class JobTracker:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_job(self, company: str, role: str, platform: str = "unknown", job_url: str = "", notes: str = "") -> Job:
        job = Job(company=company, role=role, platform=platform, job_url=job_url, notes=notes, status="applied")
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def update_job_status(self, job_id: int, new_status: str) -> Job | None:
        if new_status not in VALID_JOB_STATUSES:
            raise ValueError(f"Invalid status {new_status}. Choose from {sorted(VALID_JOB_STATUSES)}")
        job = await self.session.get(Job, job_id)
        if job is None:
            return None
        job.status = new_status
        job.last_updated = utc_now()
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def set_follow_up(self, job_id: int, when: datetime) -> Job | None:
        job = await self.session.get(Job, job_id)
        if job is None:
            return None
        job.next_follow_up = when
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def list_jobs(self, status_filter: str | None = None) -> list[Job]:
        statement = select(Job)
        if status_filter:
            statement = statement.where(Job.status == status_filter)
        statement = statement.order_by(Job.applied_at.desc())
        return list((await self.session.exec(statement)).all())

    async def jobs_due_for_follow_up(self, before: datetime | None = None) -> list[Job]:
        cutoff = before or datetime.now(timezone.utc)
        statement = select(Job).where(Job.next_follow_up.isnot(None), Job.next_follow_up <= cutoff)
        return list((await self.session.exec(statement)).all())

    async def job_status_counts(self) -> dict[str, int]:
        statement = select(Job.status, func.count(Job.id)).group_by(Job.status)
        rows = (await self.session.exec(statement)).all()
        counts = {status: 0 for status in VALID_JOB_STATUSES}
        for status, count in rows:
            counts[status] = count
        return counts

    async def consent_to_company(self, company: str, contact_email: str) -> Job | None:
        statement = select(Job).where(func.lower(Job.company) == company.lower()).limit(1)
        job = (await self.session.exec(statement)).first()
        if job is None:
            job = await self.add_job(company=company, role="", platform="email")
        return job


class EmailBox:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_email(self, external_id: str, subject: str, sender: str, snippet: str, thread_id: str, received_at: datetime | None = None) -> EmailRecord:
        statement = select(EmailRecord).where(EmailRecord.external_id == external_id)
        existing = (await self.session.exec(statement)).first()
        if existing:
            return existing
        email = EmailRecord(
            external_id=external_id,
            subject=subject,
            sender=sender,
            snippet=snippet,
            thread_id=thread_id,
            received_at=received_at or utc_now(),
        )
        self.session.add(email)
        await self.session.commit()
        await self.session.refresh(email)
        return email

    async def list_emails(self, limit: int = 50, unread_only: bool = False) -> list[EmailRecord]:
        statement = select(EmailRecord)
        if unread_only:
            statement = statement.where(EmailRecord.is_read == False)  # noqa: E712
        statement = statement.order_by(EmailRecord.received_at.desc()).limit(limit)
        return list((await self.session.exec(statement)).all())

    async def mark_read(self, email_id: int) -> EmailRecord | None:
        email = await self.session.get(EmailRecord, email_id)
        if email is None:
            return None
        email.is_read = True
        self.session.add(email)
        await self.session.commit()
        await self.session.refresh(email)
        return email

    async def mark_replied(self, email_id: int) -> EmailRecord | None:
        email = await self.session.get(EmailRecord, email_id)
        if email is None:
            return None
        email.is_replied = True
        self.session.add(email)
        await self.session.commit()
        await self.session.refresh(email)
        return email

    async def recent_sender_counts(self) -> dict[str, int]:
        statement = select(EmailRecord.sender, func.count(EmailRecord.id)).group_by(EmailRecord.sender).order_by(func.count(EmailRecord.id).desc()).limit(10)
        return {sender or "unknown": count for sender, count in (await self.session.exec(statement)).all()}


class ConversationLog:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(self, role: str, content: str, tool_used: str = "") -> ChatMessage:
        message = ChatMessage(role=role, content=content, tool_used=tool_used)
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def history(self, limit: int = 40) -> list[ChatMessage]:
        statement = select(ChatMessage).order_by(ChatMessage.created_at.desc()).limit(limit)
        return list(reversed((await self.session.exec(statement)).all()))


class ProfileStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def set_value(self, key: str, value: str) -> ProfileEntry:
        statement = select(ProfileEntry).where(ProfileEntry.key == key)
        entry = (await self.session.exec(statement)).first()
        if entry is None:
            entry = ProfileEntry(key=key, value=value)
        entry.value = value
        entry.updated_at = utc_now()
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_value(self, key: str) -> str | None:
        statement = select(ProfileEntry).where(ProfileEntry.key == key)
        entry = (await self.session.exec(statement)).first()
        return entry.value if entry else None

    async def all_values(self) -> dict[str, str]:
        statement = select(ProfileEntry)
        return {entry.key: entry.value for entry in (await self.session.exec(statement)).all()}