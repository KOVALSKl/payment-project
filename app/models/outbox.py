from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import OutboxStatus
from app.models.payment import Payment


class PaymentOutbox(Base):
    __tablename__ = "payment_outbox"

    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[OutboxStatus] = mapped_column(Enum(OutboxStatus), default=OutboxStatus.PENDING, server_default="'pending'")

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    payment: Mapped[Payment] = relationship(back_populates="outbox_events")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
