from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from app.core.dependencies import get_payment_service
from app.schemas.payment import CreatePaymentRequest, CreatePaymentResponse, GetPaymentResponse
from app.services.payment.client_payment_service import ClientPaymentService

router = APIRouter()


@router.post("/")
async def create_payment(
    body: CreatePaymentRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    service: Annotated[ClientPaymentService, Depends(get_payment_service)],
) -> JSONResponse:
    payment = await service.create_payment(body, idempotency_key)
    payload = CreatePaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    ).model_dump(mode="json")
    return JSONResponse(status_code=202, content=payload)


@router.get("/{payment_id}")
async def get_payment(payment_id: int, service: Annotated[ClientPaymentService, Depends(get_payment_service)]) -> JSONResponse:
    payment = await service.get_payment(payment_id)

    if payment is None:
        return JSONResponse(status_code=404, content={"detail": "Payment not found"})

    payload = GetPaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.payment_metadata,
        webhook_url=payment.webhook_url,
        failure_reason=payment.failure_reason,
    ).model_dump(mode="json")

    return JSONResponse(status_code=202, content=payload)
