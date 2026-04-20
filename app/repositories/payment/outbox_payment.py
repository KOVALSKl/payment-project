from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OutboxStatus
from app.models.outbox import PaymentOutbox
from app.repositories.payment.base import AbstractOutboxPaymentRepository


class OutboxPaymentRepository(AbstractOutboxPaymentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, payment: PaymentOutbox) -> None:
        self._session.add(payment)

    async def update(self, payment: PaymentOutbox) -> None:
        self._session.add(payment)

    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentOutbox | None:
        result = await self._session.execute(select(PaymentOutbox).where(PaymentOutbox.idempotency_key == idempotency_key))
        return result.scalars().first()

    async def claim_pending_batch(self, limit: int) -> Sequence[PaymentOutbox]:
        stmt = (
            select(PaymentOutbox)
            .where(PaymentOutbox.status == OutboxStatus.PENDING)
            .order_by(PaymentOutbox.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()