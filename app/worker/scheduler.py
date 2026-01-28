from __future__ import annotations

import asyncio
import logging

from app.db.session import SessionLocal
from app.db.repos.jobs import (
    list_pending_jobs,
    mark_job_done,
    mark_job_failed,
    mark_job_running,
    reschedule_job,
)
from app.worker.handlers import (
    handle_provision_subscription,
    handle_reconcile,
    handle_send_notifications,
    handle_sync_servers,
    handle_sync_users,
)

logger = logging.getLogger("worker")

JOB_HANDLERS = {
    "provision_subscription": handle_provision_subscription,
    "sync_servers": handle_sync_servers,
    "sync_users": handle_sync_users,
    "reconcile": handle_reconcile,
    "send_notifications": handle_send_notifications,
}


async def run_once() -> None:
    async with SessionLocal() as session:
        jobs = await list_pending_jobs(session)
        for job in jobs:
            handler = JOB_HANDLERS.get(job.job_type)
            if not handler:
                await mark_job_failed(session, job, "unknown_job_type")
                continue
            await mark_job_running(session, job)
            try:
                await handler(session, job.payload)
                await mark_job_done(session, job)
            except Exception as exc:
                if job.attempts + 1 >= job.max_attempts:
                    await mark_job_failed(session, job, str(exc))
                else:
                    delay = min(60 * (2 ** job.attempts), 900)
                    await reschedule_job(session, job, delay_seconds=delay, error=str(exc))


async def run_forever() -> None:
    while True:
        await run_once()
        await asyncio.sleep(5)
