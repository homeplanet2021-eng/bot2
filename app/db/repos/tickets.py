from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Ticket, TicketMessage


async def create_ticket(session: AsyncSession, user_id: int, status: str) -> Ticket:
    ticket = Ticket(user_id=user_id, status=status)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def add_message(session: AsyncSession, ticket_id: int, sender_tg_id: int, body: str) -> TicketMessage:
    message = TicketMessage(ticket_id=ticket_id, sender_tg_id=sender_tg_id, body=body)
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message


async def list_tickets(session: AsyncSession, user_id: int) -> list[Ticket]:
    result = await session.execute(select(Ticket).where(Ticket.user_id == user_id))
    return list(result.scalars().all())
