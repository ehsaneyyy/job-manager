import traceback

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import require_valid_api_key
from app.db.database import get_session
from app.db.models import EmailRecord
from app.tools import gmail
from app.tools.tracker import EmailBox

router = APIRouter(prefix="/api/emails", tags=["emails"], dependencies=[Depends(require_valid_api_key)])


class SyncResponse(BaseModel):
    synced_count: int
    error: str = ""


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    thread_id: str | None = None


class SentEmailResponse(BaseModel):
    message_id: str
    sent: bool


@router.post("/sync", response_model=SyncResponse)
async def sync_inbox(session: AsyncSession = Depends(get_session), unread_only: bool = True) -> SyncResponse:
    if not gmail.is_connected():
        return SyncResponse(synced_count=0, error="Gmail is not connected yet.")
    query = "is:unread" if unread_only else ""
    try:
        messages = gmail.list_messages(query=query, max_results=50)
    except Exception as exc:
        return SyncResponse(synced_count=0, error=f"Gmail sync failed: {exc}\n{traceback.format_exc()}")
    email_box = EmailBox(session)
    synced = 0
    for msg in messages:
        email = await email_box.upsert_email(
            external_id=msg["id"],
            subject=msg.get("subject", ""),
            sender=msg.get("from", ""),
            snippet=msg.get("snippet", ""),
            thread_id=msg.get("thread_id", ""),
        )
        if not msg.get("is_read", False):
            await email_box.mark_read(email.id)
        synced += 1
    return SyncResponse(synced_count=synced)


@router.get("")
async def list_emails(limit: int = 50, unread_only: bool = False, session: AsyncSession = Depends(get_session)) -> list[EmailRecord]:
    email_box = EmailBox(session)
    return await email_box.list_emails(limit=limit, unread_only=unread_only)


@router.get("/{email_id}")
async def get_email(email_id: int, session: AsyncSession = Depends(get_session)) -> EmailRecord:
    email = await session.get(EmailRecord, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/{email_id}/read")
async def mark_read(email_id: int, session: AsyncSession = Depends(get_session)) -> EmailRecord:
    email_box = EmailBox(session)
    updated = await email_box.mark_read(email_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return updated


@router.post("/send", response_model=SentEmailResponse)
async def send_email(request: SendEmailRequest) -> SentEmailResponse:
    if not gmail.is_connected():
        raise HTTPException(status_code=400, detail="Gmail is not connected yet.")
    try:
        message_id = gmail.send_email(to=request.to, subject=request.subject, body=request.body, thread_id=request.thread_id)
        return SentEmailResponse(message_id=message_id, sent=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Send failed: {exc}")