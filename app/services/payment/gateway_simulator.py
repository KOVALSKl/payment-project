from __future__ import annotations

import asyncio
import random

from app.models.enums import PaymentStatus


async def simulate_payment_gateway() -> tuple[PaymentStatus, str | None]:
    await asyncio.sleep(random.uniform(2.0, 5.0))
    if random.random() < 0.9:
        return PaymentStatus.SUCCEEDED, None
    return PaymentStatus.FAILED, "gateway_declined"
