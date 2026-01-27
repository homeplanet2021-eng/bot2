from __future__ import annotations

import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobOutbox
from app.db.repos.jobs import enqueue_job


async def enqueue_provisioning(session: AsyncSession, intent_id: str, payload: dict) -> JobOutbox:
    job = JobOutbox(
        job_type="provision_subscription",
        payload=payload,
        status="pending",
        idempotency_key=f"provision:{intent_id}",
    )
    return await enqueue_job(session, job)
