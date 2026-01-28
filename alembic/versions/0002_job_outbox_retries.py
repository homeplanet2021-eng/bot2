from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_job_outbox_retries"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("jobs", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("jobs", sa.Column("run_after", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.add_column("jobs", sa.Column("last_error", sa.String(length=2000), nullable=True))
    op.alter_column("jobs", "attempts", server_default=None)
    op.alter_column("jobs", "max_attempts", server_default=None)
    op.alter_column("jobs", "run_after", server_default=None)


def downgrade() -> None:
    op.drop_column("jobs", "last_error")
    op.drop_column("jobs", "run_after")
    op.drop_column("jobs", "max_attempts")
    op.drop_column("jobs", "attempts")
