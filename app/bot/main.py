from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers.start import router as start_router
from app.common.config import settings
from app.common.logging import setup_logging


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("bot")
    bot = Bot(token=settings.read_secret(settings.bot_token_file), parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    logger.info("bot_started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
