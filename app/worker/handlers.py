from __future__ import annotations

import logging

from aiogram import Bot

from app.common.config import settings
from app.common.time import utcnow
from app.db.models import JobOutbox
from app.db.repos.jobs import enqueue_job_safe
from app.db.repos.notifications import add_notification, has_notification
from app.db.repos.subscriptions import get_subscription, list_all_subscriptions, update_subscription
from app.integrations.remnawave.service import RemnawaveService
from app.notifications.service import schedule_notifications
from app.provisioning.worker_exec import execute_provisioning

logger = logging.getLogger("worker.handlers")


async def handle_provision_subscription(session, payload: dict) -> None:
    await execute_provisioning(session, payload)


async def handle_sync_servers(session, payload: dict) -> None:
    service = RemnawaveService()
    servers = await service.sync_servers()
    logger.info("sync_servers_done", extra={"extra": {"count": len(servers)}})


async def handle_sync_users(session, payload: dict) -> None:
    service = RemnawaveService()
    users = await service.sync_users()
    logger.info("sync_users_done", extra={"extra": {"count": len(users)}})


async def handle_reconcile(session, payload: dict) -> None:
    subscriptions = await list_all_subscriptions(session)
    for sub in subscriptions:
        if sub.status == "active" and sub.expires_at <= utcnow():
            sub.status = "expired"
            await update_subscription(session, sub)
        if settings.notifications_enabled and sub.status == "active":
            notices = await schedule_notifications(session, sub)
            for notice in notices:
                job = JobOutbox(
                    job_type="send_notifications",
                    payload={"kind": "subscription_notice", "user_id": sub.user_id, "subscription_id": sub.id, "notice_type": notice},
                    status="pending",
                    idempotency_key=f"notice:{sub.id}:{notice}",
                )
                await enqueue_job_safe(session, job)
    logger.info("reconcile_done", extra={"extra": {"count": len(subscriptions)}})


async def handle_send_notifications(session, payload: dict) -> None:
    kind = payload.get("kind")
    user_id = payload.get("user_id")
    if not user_id:
        return
    bot = Bot(token=settings.read_secret(settings.bot_token_file))
    if kind == "delivery_link":
        subscription_id = payload.get("subscription_id")
        subscription = await get_subscription(session, subscription_id, user_id)
        if not subscription:
            await bot.send_message(user_id, "Подписка не найдена.")
            return
        rem_user_id = subscription.provision_meta.get("remnawave_user_id")
        if not rem_user_id:
            await bot.send_message(user_id, "Ссылка подключения будет доступна после синхронизации.")
            return
        service = RemnawaveService()
        link_payload = await service.get_delivery_link(rem_user_id)
        link = link_payload.get("url") or link_payload.get("link") or "-"
        await bot.send_message(user_id, f"Ваша ссылка подключения: {link}")
        return
    if kind == "support_reply":
        text = payload.get("text") or "Ответ поддержки готов."
        await bot.send_message(user_id, text)
        return
    if kind == "subscription_notice":
        subscription_id = payload.get("subscription_id")
        notice_type = payload.get("notice_type")
        if not subscription_id or not notice_type:
            return
        if await has_notification(session, user_id, subscription_id, notice_type):
            return
        await add_notification(session, user_id, subscription_id, notice_type)
        message = {
            "expires_3d": "До окончания подписки осталось 3 дня.",
            "expires_1d": "До окончания подписки остался 1 день.",
            "expired": "Подписка завершилась. Продлите доступ в разделе «Купить подписку».",
        }.get(notice_type, "Обновление подписки.")
        await bot.send_message(user_id, message)
