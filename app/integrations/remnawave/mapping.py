from __future__ import annotations

from app.integrations.remnawave.schemas import RemnawaveServer, RemnawaveUser


def map_user(payload: dict) -> RemnawaveUser:
    return RemnawaveUser(**payload)


def map_server(payload: dict) -> RemnawaveServer:
    return RemnawaveServer(**payload)
