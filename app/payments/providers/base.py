from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InvoicePayload:
    title: str
    description: str
    payload: str
    currency: str
    prices: list[dict]


class PaymentProvider:
    name: str = ""

    def create_invoice(self, intent_id: str, amount_stars: int, description: str) -> InvoicePayload:
        raise NotImplementedError
