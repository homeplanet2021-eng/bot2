from __future__ import annotations


class HorizonError(Exception):
    pass


class RemnawaveEndpointError(HorizonError):
    pass


class PaymentError(HorizonError):
    pass
