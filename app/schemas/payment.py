from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import PaymentCurrency, PaymentStatus


class CreatePaymentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: Decimal = Field(gt=0)
    currency: PaymentCurrency
    description: str
    metadata: dict = Field(default_factory=dict, alias="metadata")
    webhook_url: HttpUrl


class CreatePaymentResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: int
    status: PaymentStatus
    created_at: datetime


class GetPaymentResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: int
    status: PaymentStatus
    created_at: datetime
    processed_at: datetime | None
    amount: Decimal
    currency: PaymentCurrency
    description: str
    metadata: dict
    webhook_url: HttpUrl
    failure_reason: str | None
