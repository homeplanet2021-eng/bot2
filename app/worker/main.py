from __future__ import annotations

import asyncio
import logging

from app.common.logging import setup_logging
from app.integrations.remnawave.endpoint_map import build_endpoint_map, validate_endpoints
from app.worker.scheduler import run_forever


async def main() -> None:
    setup_logging()
    logging.getLogger("worker").info("worker_started")
    endpoints = build_endpoint_map()
    validate_endpoints(endpoints)
    await run_forever()


if __name__ == "__main__":
    asyncio.run(main())
