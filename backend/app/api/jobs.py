from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import require_valid_api_key
from app.db.database import get_session
from app.db.models import Job
from app.tools.tracker import JobTracker, VALID_JOB_STATUSES

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(require_valid_api_key)])


class JobCreate(BaseModel):
    company: str
    role: str
    platform: str = "unknown"
    job_url: str = ""
    notes: str = ""


class JobUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    next_follow_up: datetime | None = None


@router.get("")
async def list_jobs(status: str | None = None, session: AsyncSession = Depends(get_session)) -> list[Job]:
    tracker = JobTracker(session)
    return await tracker.list_jobs(status_filter=status)


@router.get("/stats")
async def job_stats(session: AsyncSession = Depends(get_session)) -> dict[str, int]:
    tracker = JobTracker(session)
    return await tracker.job_status_counts()


@router.get("/due-follow-ups")
async def due_follow_ups(session: AsyncSession = Depends(get_session)) -> list[Job]:
    tracker = JobTracker(session)
    return await tracker.jobs_due_for_follow_up()


@router.post("")
async def create_job(request: JobCreate, session: AsyncSession = Depends(get_session)) -> Job:
    tracker = JobTracker(session)
    return await tracker.add_job(
        company=request.company,
        role=request.role,
        platform=request.platform,
        job_url=request.job_url,
        notes=request.notes,
    )


@router.patch("/{job_id}")
async def update_job(job_id: int, request: JobUpdate, session: AsyncSession = Depends(get_session)) -> Job:
    tracker = JobTracker(session)
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if request.status is not None:
        if request.status not in VALID_JOB_STATUSES:
            raise HTTPException(status_code=422, detail=f"Invalid status {request.status}")
        updated = await tracker.update_job_status(job_id, request.status)
        if updated is not None:
            job = updated
    if request.notes is not None:
        job.notes = request.notes
    if request.next_follow_up is not None:
        job.next_follow_up = request.next_follow_up
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@router.delete("/{job_id}")
async def delete_job(job_id: int, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    await session.delete(job)
    await session.commit()
    return {"status": "deleted"}