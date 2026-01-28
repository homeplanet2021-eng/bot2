from __future__ import annotations

HOME = "home"
BUY = "buy"
SUBSCRIPTIONS = "subs"
DEVICES = "devices"
ADGUARD = "adguard"
REFERRAL = "ref"
PROMO = "promo"
SUPPORT = "support"
ADMIN = "admin"
FAQ = "faq"
OFFER = "offer"
PRIVACY = "privacy"
TERMS = "terms"

BUY_PLAN = "buy_plan"
BUY_LOCATION = "buy_location"
BUY_PAY = "buy_pay"
BUY_PROMO = "buy_promo"
BUY_TRIAL = "buy_trial"

SUB_VIEW = "sub_view"
SUB_LINK = "sub_link"

SUPPORT_NEW = "support_new"
SUPPORT_LIST = "support_list"
SUPPORT_VIEW = "support_view"
SUPPORT_REPLY = "support_reply"

ADMIN_TICKETS = "admin_tickets"
ADMIN_TICKET_VIEW = "admin_ticket_view"
ADMIN_TICKET_REPLY = "admin_ticket_reply"
ADMIN_SYNC_SERVERS = "admin_sync_servers"
ADMIN_SYNC_USERS = "admin_sync_users"
ADMIN_RECONCILE = "admin_reconcile"

ADGUARD_TOGGLE = "adguard_toggle"


def pack(action: str, *parts: str) -> str:
    return ":".join([action, *[str(part) for part in parts if part is not None]])


def parse(data: str) -> tuple[str, list[str]]:
    parts = data.split(":")
    return parts[0], parts[1:]
