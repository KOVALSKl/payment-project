from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from app.db.unit_of_work import AbstractUnitOfWork
from app.models.payment import Payment
from app.services.payment.gateway_simulator import simulate_payment_gateway


class PaymentProcessorService:
    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def process_payment_once(self, payment_id: int) -> Payment | None:
        async with self._uow_factory() as uow:
            payment = await uow.payments.get_by_id(payment_id)
            if payment is None:
                await uow.commit()
                return None

            # Consumer re-delivery is expected; domain processing should happen exactly once.
            if payment.processed_at is None:
                status, failure_reason = await simulate_payment_gateway()
                payment.status = status
                payment.processed_at = datetime.now(timezone.utc)
                payment.failure_reason = failure_reason
                await uow.payments.update(payment)

            await uow.commit()
            return payment
