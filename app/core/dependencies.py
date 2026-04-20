from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from app.db.base import async_session_maker
from app.db.unit_of_work import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from app.services.payment.client_payment_service import ClientPaymentService


def get_uow_factory() -> Callable[[], SqlAlchemyUnitOfWork]:
    def _factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(async_session_maker)

    return _factory


def get_payment_service(
    uow_factory: Annotated[
        Callable[[], AbstractUnitOfWork], Depends(get_uow_factory)
    ],
) -> ClientPaymentService:
    return ClientPaymentService(uow_factory)
