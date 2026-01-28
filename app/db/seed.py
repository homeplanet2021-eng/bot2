from __future__ import annotations

import asyncio
from sqlalchemy import delete

from app.common.config import settings
from app.common.time import utcnow
from app.db.session import SessionLocal
from app.db.models import ContentPage, Location, Plan, PlanLocationMapping


CONTENT_PAGES = [
    ("home", "Horizon VPN", "Добро пожаловать в Horizon VPN. Безопасный доступ, высокая скорость и поддержка 24/7."),
    (
        "faq",
        "Вопросы и ответы",
        "Подписка активируется сразу после оплаты. Ссылка подключения доступна в разделе «Подписки». "
        "Если возникли сложности, напишите в поддержку через бот.",
    ),
    (
        "offer",
        "Публичная оферта",
        "Horizon VPN предоставляет цифровую услугу доступа к VPN. Доступ активируется сразу после оплаты. "
        "Используйте сервис в рамках законодательства и правил сервиса.",
    ),
    (
        "privacy",
        "Политика конфиденциальности",
        "Мы не сохраняем содержимое трафика. Мы используем минимальные данные для предоставления услуги и поддержки.",
    ),
    (
        "terms",
        "Правила сервиса",
        "Запрещены злоупотребления, DDoS, спам и незаконный контент. "
        "Нарушения ведут к блокировке без компенсации.",
    ),
]


async def seed() -> None:
    async with SessionLocal() as session:
        await session.execute(delete(PlanLocationMapping))
        await session.execute(delete(Location))
        await session.execute(delete(Plan))
        await session.execute(delete(ContentPage))
        await session.commit()

        plans = [
            Plan(plan_code="classic", title="Classic", duration_days=30, price_stars=199, device_limit=3, is_active=True),
            Plan(plan_code="premium", title="Premium", duration_days=30, price_stars=299, device_limit=5, is_active=True),
        ]
        locations = [
            Location(code="nl1", title="Netherlands", is_active=True),
            Location(code="de1", title="Germany", is_active=True),
            Location(code="fr1", title="France", is_active=True),
        ]
        session.add_all(plans)
        session.add_all(locations)
        await session.commit()

        mapping = [
            PlanLocationMapping(
                plan_code="classic",
                location_code="nl1",
                remnawave_profile_uuid=settings.hzn_profile_classic_uuid,
                optional_squad_id=None,
                is_active=True,
            ),
            PlanLocationMapping(
                plan_code="classic",
                location_code="de1",
                remnawave_profile_uuid=settings.hzn_profile_classic_uuid,
                optional_squad_id=None,
                is_active=True,
            ),
            PlanLocationMapping(
                plan_code="classic",
                location_code="fr1",
                remnawave_profile_uuid=settings.hzn_profile_classic_uuid,
                optional_squad_id=None,
                is_active=True,
            ),
            PlanLocationMapping(
                plan_code="premium",
                location_code="nl1",
                remnawave_profile_uuid=settings.hzn_profile_premium_uuid,
                optional_squad_id=None,
                is_active=True,
            ),
            PlanLocationMapping(
                plan_code="premium",
                location_code="de1",
                remnawave_profile_uuid=settings.hzn_profile_premium_uuid,
                optional_squad_id=None,
                is_active=True,
            ),
            PlanLocationMapping(
                plan_code="premium",
                location_code="fr1",
                remnawave_profile_uuid=settings.hzn_profile_premium_uuid,
                optional_squad_id=None,
                is_active=True,
            ),
        ]
        session.add_all(mapping)
        await session.commit()

        pages = [ContentPage(key=key, title=title, body_md=body, updated_at=utcnow()) for key, title, body in CONTENT_PAGES]
        session.add_all(pages)
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
