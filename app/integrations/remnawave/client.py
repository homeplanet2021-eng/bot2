from __future__ import annotations

import asyncio
from typing import Any, Dict

import httpx

from app.common.config import settings


class RemnawaveClient:
    def __init__(self) -> None:
        self.base_url = settings.remnawave_base_url.rstrip("/")
        self.token = settings.read_secret(settings.remnawave_token_file)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def request(self, method: str, path: str, json: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=10) as client:
            for attempt in range(3):
                try:
                    response = await client.request(method, url, headers=self._headers(), json=json)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1 + attempt)
