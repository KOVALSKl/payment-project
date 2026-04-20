from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment

from .base import AbstractPaymentRepository


class PaymentAlchemyRepository(AbstractPaymentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, payment: Payment) -> None:
        self._session.add(payment)

    async def update(self, payment: Payment) -> None:
        self._session.add(payment)

    async def get_by_id(self, payment_id: int) -> Payment | None:
        result =  await self._session.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalars().first()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        result = await self._session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
        return result.scalars().first()