from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobOutbox


async def enqueue_job(session: AsyncSession, job: JobOutbox) -> JobOutbox:
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def enqueue_job_safe(session: AsyncSession, job: JobOutbox) -> JobOutbox:
    session.add(job)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        result = await session.execute(select(JobOutbox).where(JobOutbox.idempotency_key == job.idempotency_key))
        existing = result.scalar_one()
        return existing
    await session.refresh(job)
    return job


async def list_pending_jobs(session: AsyncSession, limit: int = 50) -> list[JobOutbox]:
    result = await session.execute(
        select(JobOutbox)
        .where(JobOutbox.status == "pending")
        .where(JobOutbox.run_after <= sa.func.now())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_job_running(session: AsyncSession, job: JobOutbox) -> JobOutbox:
    job.status = "running"
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_job_done(session: AsyncSession, job: JobOutbox) -> JobOutbox:
    job.status = "done"
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def mark_job_failed(session: AsyncSession, job: JobOutbox, error: str) -> JobOutbox:
    job.status = "failed"
    job.last_error = error[:2000]
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def reschedule_job(session: AsyncSession, job: JobOutbox, delay_seconds: int, error: str) -> JobOutbox:
    job.attempts += 1
    job.last_error = error[:2000]
    job.status = "pending"
    job.run_after = sa.func.now() + sa.text(f"interval '{delay_seconds} seconds'")
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job
