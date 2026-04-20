from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PaymentCurrency, PaymentStatus

if TYPE_CHECKING:
    from app.models.outbox import PaymentOutbox


class Payment(Base):
    __tablename__ = "payments"

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    currency: Mapped[PaymentCurrency] = mapped_column(Enum(PaymentCurrency))
    description: Mapped[str] = mapped_column(Text)
    payment_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, server_default="'pending'")
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    webhook_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    outbox_events: Mapped[list["PaymentOutbox"]] = relationship(back_populates="payment")
