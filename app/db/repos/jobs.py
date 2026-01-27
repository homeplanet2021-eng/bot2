from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobOutbox


async def enqueue_job(session: AsyncSession, job: JobOutbox) -> JobOutbox:
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def list_pending_jobs(session: AsyncSession, limit: int = 50) -> list[JobOutbox]:
    result = await session.execute(select(JobOutbox).where(JobOutbox.status == "pending").limit(limit))
    return list(result.scalars().all())
