from __future__ import annotations

import asyncio
import logging

from app.db.session import SessionLocal
from app.db.repos.jobs import list_pending_jobs
from app.provisioning.worker_exec import execute_provisioning

logger = logging.getLogger("worker")


async def run_once() -> None:
    async with SessionLocal() as session:
        jobs = await list_pending_jobs(session)
        for job in jobs:
            if job.job_type == "provision_subscription":
                await execute_provisioning(session, job.payload)
                job.status = "done"
                session.add(job)
                await session.commit()


async def run_forever() -> None:
    while True:
        await run_once()
        await asyncio.sleep(5)
