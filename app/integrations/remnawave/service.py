from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from app.common.config import settings
from app.common.errors import RemnawaveEndpointError
from app.integrations.remnawave.client import RemnawaveClient
from app.integrations.remnawave.endpoint_map import build_endpoint_map, validate_endpoints
from app.integrations.remnawave.mapping import map_server, map_user


class RemnawaveService:
    def __init__(self) -> None:
        self.client = RemnawaveClient()
        self.endpoints = build_endpoint_map()
        validate_endpoints(self.endpoints)

    def _path(self, name: str, **kwargs: Any) -> str:
        if name not in self.endpoints:
            raise RemnawaveEndpointError(f"Unknown endpoint {name}")
        return self.endpoints[name].format(**kwargs)

    async def ensure_user(self, username: str) -> dict:
        path = self._path("create_user")
        return await self.client.request("POST", path, json={"username": username})

    async def apply_access(self, user_id: str, profile_uuid: str, expires_at: datetime) -> dict:
        path = self._path("update_user", user_id=user_id)
        return await self.client.request(
            "PATCH",
            path,
            json={"profile_uuid": profile_uuid, "expires_at": expires_at.isoformat()},
        )

    async def extend_expiration(self, user_id: str, days: int) -> dict:
        path = self._path("extend_expiration", user_id=user_id)
        return await self.client.request("POST", path, json={"days": days})

    async def get_delivery_link(self, user_id: str) -> dict:
        path = self._path("get_delivery_link", user_id=user_id)
        return await self.client.request("GET", path)

    async def sync_servers(self) -> list[dict]:
        path = self._path("sync_servers")
        payload = await self.client.request("GET", path)
        return [map_server(item).model_dump() for item in payload]

    async def sync_users(self) -> list[dict]:
        path = self._path("sync_users")
        payload = await self.client.request("GET", path)
        return [map_user(item).model_dump() for item in payload]
