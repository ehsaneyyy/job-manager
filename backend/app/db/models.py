from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    company: str = Field(index=True)
    role: str
    platform: str = "unknown"
    job_url: str = ""
    status: str = Field(default="applied", index=True)
    applied_at: datetime = Field(default_factory=utc_now)
    last_updated: datetime = Field(default_factory=utc_now)
    next_follow_up: datetime | None = None
    notes: str = ""
    meta: str = "{}"


class EmailRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    external_id: str = Field(unique=True, index=True)
    subject: str = ""
    sender: str = ""
    snippet: str = ""
    summary: str = ""
    thread_id: str = ""
    received_at: datetime = Field(default_factory=utc_now)
    is_read: bool = Field(default=False, index=True)
    is_replied: bool = Field(default=False, index=True)


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: str
    content: str
    tool_used: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ProfileEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))


class SyncRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(index=True)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    count: int = 0
    status: str = "running"