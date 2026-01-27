from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RemnawaveEndpointOverrides(BaseModel):
    overrides: Dict[str, str] = {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tz: str = "UTC"
    bot_token_file: str
    admin_tg_ids: str
    database_url: str
    redis_url: str

    remnawave_base_url: str
    remnawave_token_file: str
    remnawave_webhook_enabled: bool = False
    remnawave_webhook_path: str = "/webhooks/remnawave"
    remnawave_webhook_secret_file: str
    remnawave_api_mode: str = "strict"
    remnawave_endpoint_overrides_json: str = "{}"

    hzn_profile_classic_uuid: str
    hzn_profile_premium_uuid: str

    sub_public_domain: str

    adguard_enabled: bool = False
    adguard_dns_primary: str = ""
    adguard_dns_secondary: str = ""

    cabinet_enabled: bool = False
    cabinet_public_url: str = ""
    cabinet_jwt_secret_file: str = ""

    notifications_enabled: bool = True
    maintenance_mode: bool = False

    def admin_ids(self) -> List[int]:
        return [int(value.strip()) for value in self.admin_tg_ids.split(",") if value.strip()]

    def read_secret(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8").strip()

    def remnawave_overrides(self) -> Dict[str, str]:
        try:
            data = json.loads(self.remnawave_endpoint_overrides_json or "{}")
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items()}


settings = Settings()
