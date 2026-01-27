from __future__ import annotations

from app.payments.providers.base import InvoicePayload, PaymentProvider


class ManualProvider(PaymentProvider):
    name = "manual"

    def create_invoice(self, intent_id: str, amount_stars: int, description: str) -> InvoicePayload:
        return InvoicePayload(
            title="Horizon VPN",
            description=f"Manual payment: {description}",
            payload=intent_id,
            currency="XTR",
            prices=[{"label": "Stars", "amount": amount_stars}],
        )
