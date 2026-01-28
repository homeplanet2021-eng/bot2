from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers.payments import router as payments_router
from app.bot.handlers.start import router as start_router
from app.common.config import settings
from app.common.logging import setup_logging


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("bot")
    bot = Bot(token=settings.read_secret(settings.bot_token_file), parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(payments_router)
    logger.info("bot_started")
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as exc:
            logger.error("bot_polling_error", extra={"extra": {"error": str(exc)}})
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
