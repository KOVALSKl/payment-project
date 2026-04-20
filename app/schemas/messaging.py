from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models.enums import PaymentCurrency, PaymentStatus


class PaymentNewPayload(BaseModel):
    payment_id: int
    amount: Decimal
    currency: PaymentCurrency
    webhook_url: HttpUrl


class PaymentNewEvent(BaseModel):
    event_type: str
    payload: PaymentNewPayload
    idempotency_key: str
    payment_id: int


class WebhookNotificationPayload(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: int
    status: PaymentStatus
    amount: Decimal
    currency: PaymentCurrency
    processed_at: datetime | None
    idempotency_key: str
    error: str | None = None
