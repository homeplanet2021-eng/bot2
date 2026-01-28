from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.ui import callbacks


def home_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🛒 Купить подписку", callback_data=callbacks.BUY)],
        [InlineKeyboardButton(text="👤 Подписки", callback_data=callbacks.SUBSCRIPTIONS)],
        [InlineKeyboardButton(text="📱 Устройства", callback_data=callbacks.DEVICES)],
        [InlineKeyboardButton(text="🛡 AdGuard DNS", callback_data=callbacks.ADGUARD)],
        [InlineKeyboardButton(text="🎁 Рефералы", callback_data=callbacks.REFERRAL)],
        [InlineKeyboardButton(text="🏷 Промокод", callback_data=callbacks.PROMO)],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data=callbacks.SUPPORT)],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data=callbacks.FAQ),
            InlineKeyboardButton(text="📄 Оферта", callback_data=callbacks.OFFER),
        ],
        [
            InlineKeyboardButton(text="🔒 Конфиденциальность", callback_data=callbacks.PRIVACY),
            InlineKeyboardButton(text="⚖️ Правила", callback_data=callbacks.TERMS),
        ],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🧑‍💼 Админ", callback_data=callbacks.ADMIN)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)]]
    )


def buy_keyboard(include_trial: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📄 Выбрать тариф", callback_data=callbacks.BUY_PLAN)],
        [InlineKeyboardButton(text="🏷 Ввести промокод", callback_data=callbacks.BUY_PROMO)],
        [InlineKeyboardButton(text="💫 Оплатить Stars", callback_data=callbacks.BUY_PAY)],
    ]
    if include_trial:
        buttons.append([InlineKeyboardButton(text="🆓 Пробный период 24ч", callback_data=callbacks.BUY_TRIAL)])
    buttons.append([InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Создать обращение", callback_data=callbacks.SUPPORT_NEW)],
            [InlineKeyboardButton(text="📂 Мои обращения", callback_data=callbacks.SUPPORT_LIST)],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)],
        ]
    )


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📂 Тикеты", callback_data=callbacks.ADMIN_TICKETS)],
            [InlineKeyboardButton(text="🔄 Sync servers", callback_data=callbacks.ADMIN_SYNC_SERVERS)],
            [InlineKeyboardButton(text="🔄 Sync users", callback_data=callbacks.ADMIN_SYNC_USERS)],
            [InlineKeyboardButton(text="🧹 Reconcile", callback_data=callbacks.ADMIN_RECONCILE)],
            [InlineKeyboardButton(text="⬅️ Главное меню", callback_data=callbacks.HOME)],
        ]
    )
