from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("tg_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referrer_id", sa.Integer(), nullable=True),
        sa.Column("ref_code", sa.String(length=16), nullable=False, unique=True),
        sa.Column("trial_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("adguard_enabled", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "plans",
        sa.Column("plan_code", sa.String(length=32), primary_key=True),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_stars", sa.Integer(), nullable=False),
        sa.Column("device_limit", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "locations",
        sa.Column("code", sa.String(length=16), primary_key=True),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "plan_location_mapping",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_code", sa.String(length=32), nullable=False),
        sa.Column("location_code", sa.String(length=16), nullable=False),
        sa.Column("remnawave_profile_uuid", sa.String(length=64), nullable=False),
        sa.Column("optional_squad_id", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["plan_code"], ["plans.plan_code"]),
        sa.ForeignKeyConstraint(["location_code"], ["locations.code"]),
        sa.UniqueConstraint("plan_code", "location_code", name="uq_plan_location"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(length=32), nullable=False),
        sa.Column("location_code", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provision_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
        sa.ForeignKeyConstraint(["plan_code"], ["plans.plan_code"]),
        sa.ForeignKeyConstraint(["location_code"], ["locations.code"]),
    )

    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("discount_percent", sa.Integer(), nullable=True),
        sa.Column("discount_stars", sa.Integer(), nullable=True),
        sa.Column("free_days", sa.Integer(), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "payment_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(length=32), nullable=False),
        sa.Column("period_days", sa.Integer(), nullable=False),
        sa.Column("location_code", sa.String(length=16), nullable=False),
        sa.Column("amount_stars", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("promo_code_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
        sa.ForeignKeyConstraint(["plan_code"], ["plans.plan_code"]),
        sa.ForeignKeyConstraint(["location_code"], ["locations.code"]),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"]),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("intent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=128), nullable=True, unique=True),
        sa.Column("amount_stars", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["intent_id"], ["payment_intents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
        sa.ForeignKeyConstraint(["plan_code"], ["plans.plan_code"]),
    )

    op.create_table(
        "promo_redemptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("promo_code_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
        sa.UniqueConstraint("promo_code_id", "user_id", name="uq_promo_user"),
    )

    op.create_table(
        "referral_earnings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("referrer_id", sa.Integer(), nullable=False),
        sa.Column("referred_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_stars", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["referrer_id"], ["users.tg_id"]),
        sa.ForeignKeyConstraint(["referred_id"], ["users.tg_id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.UniqueConstraint("payment_id", name="uq_referral_payment"),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
    )

    op.create_table(
        "ticket_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("sender_tg_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
    )

    op.create_table(
        "notifications_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.tg_id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.UniqueConstraint("user_id", "subscription_id", "type", name="uq_notification"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_job_idem"),
    )

    op.create_table(
        "content_pages",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("body_md", sa.String(length=6000), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "admin_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_tg_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("admin_audit")
    op.drop_table("content_pages")
    op.drop_table("jobs")
    op.drop_table("notifications_log")
    op.drop_table("ticket_messages")
    op.drop_table("tickets")
    op.drop_table("referral_earnings")
    op.drop_table("promo_redemptions")
    op.drop_table("payments")
    op.drop_table("payment_intents")
    op.drop_table("promo_codes")
    op.drop_table("subscriptions")
    op.drop_table("plan_location_mapping")
    op.drop_table("locations")
    op.drop_table("plans")
    op.drop_table("users")
