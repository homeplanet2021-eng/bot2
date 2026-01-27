from __future__ import annotations

from pydantic import BaseModel


class RemnawaveUser(BaseModel):
    id: str
    username: str
    expires_at: str | None = None


class RemnawaveServer(BaseModel):
    id: str
    name: str
