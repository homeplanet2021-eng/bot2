from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.time import utcnow
from app.db.models import Subscription
from app.db.repos.locations import get_mapping
from app.db.repos.subscriptions import create_subscription
from app.integrations.remnawave.service import RemnawaveService


async def execute_provisioning(session: AsyncSession, payload: dict) -> Subscription:
    user_id = payload["user_id"]
    plan_code = payload["plan_code"]
    location_code = payload["location_code"]
    period_days = payload["period_days"]

    mapping = await get_mapping(session, plan_code, location_code)
    if not mapping:
        raise ValueError("Missing plan location mapping")

    service = RemnawaveService()
    rem_user = await service.ensure_user(username=str(user_id))
    expires_at = utcnow() + timedelta(days=period_days)
    await service.apply_access(rem_user["id"], mapping.remnawave_profile_uuid, expires_at)
    await service.get_delivery_link(rem_user["id"])

    return await create_subscription(
        session,
        user_id=user_id,
        plan_code=plan_code,
        location_code=location_code,
        expires_at=expires_at,
        status="active",
        provision_meta={"remnawave_user_id": rem_user["id"]},
    )
