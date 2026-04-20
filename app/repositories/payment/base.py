from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.models.outbox import PaymentOutbox
from app.models.payment import Payment


class AbstractPaymentRepository(ABC):
    @abstractmethod
    async def add(self, payment: Payment) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, payment: Payment) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, payment_id: int) -> Payment | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        raise NotImplementedError


class AbstractOutboxPaymentRepository(ABC):
    @abstractmethod
    async def add(self, payment: PaymentOutbox) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, payment: PaymentOutbox) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentOutbox | None:
        raise NotImplementedError

    @abstractmethod
    async def claim_pending_batch(self, limit: int) -> Sequence[PaymentOutbox]:
        """Строки outbox со статусом pending под блокировкой FOR UPDATE SKIP LOCKED."""
        raise NotImplementedError
