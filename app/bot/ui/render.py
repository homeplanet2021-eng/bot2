from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

ROOT_MESSAGE: dict[int, int] = {}


async def ensure_root(
    bot: Bot,
    chat_id: int,
    user_id: int,
    text: str,
    reply_markup: object | None = None,
) -> int:
    if user_id in ROOT_MESSAGE:
        message_id = ROOT_MESSAGE[user_id]
        await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
        return message_id
    sent = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    ROOT_MESSAGE[user_id] = sent.message_id
    return sent.message_id


def sync_root(user_id: int, message_id: int) -> None:
    ROOT_MESSAGE[user_id] = message_id
