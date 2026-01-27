from __future__ import annotations

from typing import Dict

from app.common.config import settings
from app.common.errors import RemnawaveEndpointError


DEFAULT_ENDPOINTS: Dict[str, str] = {
    "create_user": "/api/users",
    "update_user": "/api/users/{user_id}",
    "extend_expiration": "/api/users/{user_id}/extend",
    "get_delivery_link": "/api/users/{user_id}/delivery",
    "sync_servers": "/api/servers",
    "sync_users": "/api/users",
}


def build_endpoint_map() -> Dict[str, str]:
    overrides = settings.remnawave_overrides()
    endpoints = {**DEFAULT_ENDPOINTS}
    endpoints.update(overrides)
    return endpoints


def validate_endpoints(endpoints: Dict[str, str]) -> None:
    missing = [name for name, path in endpoints.items() if not path or not path.startswith("/")]
    if missing:
        raise RemnawaveEndpointError(f"Invalid Remnawave endpoints: {missing}")

    if settings.remnawave_api_mode == "strict":
        unknown = [name for name in endpoints.keys() if name not in DEFAULT_ENDPOINTS]
        if unknown:
            raise RemnawaveEndpointError(f"Unknown endpoint overrides not allowed in strict mode: {unknown}")
