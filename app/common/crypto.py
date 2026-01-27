from __future__ import annotations

import hashlib
import secrets


def make_ref_code(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_payload(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
