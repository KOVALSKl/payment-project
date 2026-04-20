from collections.abc import Callable

from sqlalchemy.exc import IntegrityError

from app.db.unit_of_work import AbstractUnitOfWork
from app.models.enums import OutboxStatus, PaymentStatus
from app.models.outbox import PaymentOutbox
from app.models.payment import Payment
from app.schemas.payment import CreatePaymentRequest


class ClientPaymentService:
    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def create_payment(
        self, data: CreatePaymentRequest, idempotency_key: str
    ) -> Payment:
        try:
            async with self._uow_factory() as uow:
                existing = await uow.payments.get_by_idempotency_key(idempotency_key)
                if existing is not None:
                    await uow.commit()
                    return existing

                payment = Payment(
                    amount=data.amount,
                    currency=data.currency,
                    description=data.description,
                    payment_metadata=dict(data.metadata),
                    idempotency_key=idempotency_key,
                    webhook_url=str(data.webhook_url),
                    status=PaymentStatus.PENDING,
                )
                await uow.payments.add(payment)
                await uow.flush()

                outbox = PaymentOutbox(
                    event_type="payment.new",
                    payload={
                        "payment_id": payment.id,
                        "amount": str(payment.amount),
                        "currency": payment.currency.value,
                        "webhook_url": payment.webhook_url,
                    },
                    idempotency_key=idempotency_key,
                    payment_id=payment.id,
                    status=OutboxStatus.PENDING,
                )
                await uow.outbox.add(outbox)
                await uow.commit()
                return payment
        except IntegrityError:
            async with self._uow_factory() as uow:
                existing = await uow.payments.get_by_idempotency_key(idempotency_key)
                if existing is not None:
                    await uow.commit()
                    return existing
            raise

    async def get_payment(self, payment_id: int) -> Payment | None:
        async with self._uow_factory() as uow:
            return await uow.payments.get_by_id(payment_id)