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


async def list_tickets(session: AsyncSession, user_id: int | None) -> list[Ticket]:
    query = select(Ticket)
    if user_id is not None:
        query = query.where(Ticket.user_id == user_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_ticket(session: AsyncSession, ticket_id: int, user_id: int | None) -> Ticket | None:
    query = select(Ticket).where(Ticket.id == ticket_id)
    if user_id is not None:
        query = query.where(Ticket.user_id == user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_ticket_messages(session: AsyncSession, ticket_id: int) -> list[TicketMessage]:
    result = await session.execute(select(TicketMessage).where(TicketMessage.ticket_id == ticket_id))
    return list(result.scalars().all())


async def update_ticket_status(session: AsyncSession, ticket: Ticket, status: str) -> Ticket:
    ticket.status = status
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket
