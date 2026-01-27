from __future__ import annotations

import asyncio
import logging

from app.common.logging import setup_logging
from app.integrations.remnawave.service import RemnawaveService


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("remnawave.check")
    service = RemnawaveService()
    servers = await service.sync_servers()
    logger.info("remnawave_check", extra={"extra": {"servers": len(servers)}})


if __name__ == "__main__":
    asyncio.run(main())
