"""init payments and outbox

Revision ID: 20260420_000001
Revises:
Create Date: 2026-04-20 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260420_000001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


payment_currency_enum = postgresql.ENUM(
    "RUB",
    "USD",
    "EUR",
    name="paymentcurrency",
    create_type=False,
)
payment_status_enum = postgresql.ENUM(
    "pending",
    "succeeded",
    "failed",
    name="paymentstatus",
    create_type=False,
)
outbox_status_enum = postgresql.ENUM(
    "pending",
    "published",
    "failed",
    name="outboxstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    payment_currency_enum.create(bind, checkfirst=True)
    payment_status_enum.create(bind, checkfirst=True)
    outbox_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "payments",
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", payment_currency_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "payment_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "status",
            payment_status_enum,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("webhook_url", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )

    op.create_table(
        "payment_outbox",
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "status",
            outbox_status_enum,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        op.f("ix_payment_outbox_payment_id"),
        "payment_outbox",
        ["payment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_outbox_payment_id"), table_name="payment_outbox")
    op.drop_table("payment_outbox")
    op.drop_table("payments")

    bind = op.get_bind()
    outbox_status_enum.drop(bind, checkfirst=True)
    payment_status_enum.drop(bind, checkfirst=True)
    payment_currency_enum.drop(bind, checkfirst=True)
