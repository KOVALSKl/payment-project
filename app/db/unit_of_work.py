from abc import ABC, abstractmethod
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.payment.base import (
    AbstractOutboxPaymentRepository,
    AbstractPaymentRepository,
)
from app.repositories.payment.client_payment import PaymentAlchemyRepository
from app.repositories.payment.outbox_payment import OutboxPaymentRepository


class AbstractUnitOfWork(ABC):
    payments: AbstractPaymentRepository
    outbox: AbstractOutboxPaymentRepository

    @abstractmethod
    async def __aenter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def flush(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.payments = PaymentAlchemyRepository(self._session)
        self.outbox = OutboxPaymentRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session is None:
            return
        if exc_type is not None:
            await self._session.rollback()
        await self._session.close()
        self._session = None

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used as an async context manager")
        await self._session.commit()

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used as an async context manager")
        await self._session.rollback()

    async def flush(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used as an async context manager")
        await self._session.flush()
