from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from app.bot.ui.keyboards import home_keyboard
from app.bot.ui.texts import HOME_TEXT


async def render_home(bot: Bot, message: Message) -> None:
    await bot.edit_message_text(
        text=HOME_TEXT,
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=home_keyboard(),
    )
