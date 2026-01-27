from __future__ import annotations

import logging
from fastapi import Depends, FastAPI, Header, HTTPException, Request

from app.common.config import settings
from app.common.logging import setup_logging
from app.db.session import get_session
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
    logger.info("remnawave_webhook", extra={"extra": {"payload": payload}})
    return {"status": "accepted"}
