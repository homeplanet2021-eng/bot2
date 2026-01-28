from __future__ import annotations

import hashlib
import json
import logging
from fastapi import FastAPI, Header, HTTPException, Request

from app.common.config import settings
from app.common.logging import setup_logging
from app.db.models import JobOutbox
from app.db.repos.jobs import enqueue_job_safe
from app.db.session import SessionLocal
from app.integrations.remnawave.endpoint_map import build_endpoint_map, validate_endpoints


setup_logging()
logger = logging.getLogger("api")

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    endpoints = build_endpoint_map()
    validate_endpoints(endpoints)
    logger.info("remnawave_endpoint_check", extra={"extra": {"mode": settings.remnawave_api_mode}})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post(settings.remnawave_webhook_path)
async def remnawave_webhook(request: Request, x_signature: str | None = Header(default=None)) -> dict:
    if not settings.remnawave_webhook_enabled:
        raise HTTPException(status_code=404, detail="disabled")
    secret = settings.read_secret(settings.remnawave_webhook_secret_file)
    if x_signature != secret:
        raise HTTPException(status_code=403, detail="forbidden")
    payload = await request.json()
    event = str(payload.get("type") or payload.get("event") or "")
    resource = str(payload.get("resource") or "")
    if "server" in event or "server" in resource:
        job_type = "sync_servers"
    elif "user" in event or "user" in resource:
        job_type = "sync_users"
    else:
        job_type = "reconcile"
    payload_id = payload.get("id") or payload.get("event_id")
    if payload_id:
        idem = f"webhook:{job_type}:{payload_id}"
    else:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        idem = f"webhook:{job_type}:{digest}"
    async with SessionLocal() as session:
        job = JobOutbox(
            job_type=job_type,
            payload={"source": "remnawave", "payload": payload},
            status="pending",
            idempotency_key=idem,
        )
        await enqueue_job_safe(session, job)
    logger.info("remnawave_webhook_enqueued", extra={"extra": {"job_type": job_type, "id": idem}})
    return {"status": "accepted"}
