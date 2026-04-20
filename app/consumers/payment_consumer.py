from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from faststream.rabbit.message import RabbitMessage

from app.core.config import rabbitmq_config
from app.db.base import async_session_maker
from app.db.unit_of_work import AbstractUnitOfWork, SqlAlchemyUnitOfWork
from app.messaging.rabbitmq_retry import publish_dlq_event, publish_retry_event
from app.schemas.messaging import PaymentNewEvent, WebhookNotificationPayload
from app.services.payment.processor import PaymentProcessorService
from app.services.webhook_sender import WebhookDeliveryError, send_webhook

logger = logging.getLogger(__name__)

broker = RabbitBroker(rabbitmq_config.RABBITMQ_URL)
app = FastStream(broker)


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(async_session_maker)


def _retry_delay_seconds(attempt: int) -> int:
    # attempt=2 -> base*1, attempt=3 -> base*2
    exponent = max(0, attempt - 2)
    return rabbitmq_config.RETRY_BASE_DELAY_SECONDS * (2**exponent)


def _extract_attempt(headers: dict[str, Any] | None) -> int:
    if not headers:
        return 1
    attempt = headers.get("x-attempt", 1)
    try:
        attempt_int = int(attempt)
    except (TypeError, ValueError):
        return 1
    return max(1, attempt_int)


async def _publish_retry(
    *,
    body: dict[str, Any],
    attempt: int,
    error: str,
) -> None:
    delay_seconds = _retry_delay_seconds(attempt)
    await asyncio.to_thread(
        publish_retry_event,
        body,
        rabbitmq_url=rabbitmq_config.RABBITMQ_URL,
        main_queue=rabbitmq_config.PAYMENTS_NEW_QUEUE,
        retry_queue=rabbitmq_config.PAYMENTS_RETRY_QUEUE,
        delay_seconds=delay_seconds,
        attempt=attempt,
        error=error,
    )
    logger.warning(
        "Webhook failed. Scheduled retry attempt=%s delay_seconds=%s",
        attempt,
        delay_seconds,
    )


async def _publish_dlq(
    *,
    body: dict[str, Any],
    attempt: int,
    error: str,
) -> None:
    await asyncio.to_thread(
        publish_dlq_event,
        body,
        rabbitmq_url=rabbitmq_config.RABBITMQ_URL,
        dlq_queue=rabbitmq_config.PAYMENTS_DLQ_QUEUE,
        attempt=attempt,
        error=error,
        original_queue=rabbitmq_config.PAYMENTS_NEW_QUEUE,
    )
    logger.error("Message moved to DLQ after attempt=%s error=%s", attempt, error)


@broker.subscriber(rabbitmq_config.PAYMENTS_NEW_QUEUE)
async def consume_payment_event(event: dict[str, Any], message: RabbitMessage) -> None:
    attempt = _extract_attempt(message.headers)
    logger.info("Consumed payment event, attempt=%s payload=%s", attempt, event)

    try:
        parsed = PaymentNewEvent.model_validate(event)
    except Exception as exc:  # noqa: BLE001
        error = f"invalid_payload: {exc}"
        await _publish_dlq(body=event, attempt=attempt, error=error)
        return

    processor = PaymentProcessorService(_uow_factory)
    payment = await processor.process_payment_once(parsed.payment_id)
    if payment is None:
        error = f"payment_not_found:{parsed.payment_id}"
        await _publish_dlq(body=event, attempt=attempt, error=error)
        return

    webhook_payload = WebhookNotificationPayload(
        payment_id=payment.id,
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        processed_at=payment.processed_at,
        idempotency_key=payment.idempotency_key,
        error=payment.failure_reason,
    ).model_dump(mode="json")

    try:
        await send_webhook(payment.webhook_url, webhook_payload)
        logger.info("Webhook sent successfully payment_id=%s", payment.id)
        return
    except WebhookDeliveryError as exc:
        error = str(exc)
    except Exception as exc:  # noqa: BLE001
        error = f"webhook_unexpected_error:{exc}"

    next_attempt = attempt + 1
    if next_attempt <= rabbitmq_config.WEBHOOK_MAX_ATTEMPTS:
        await _publish_retry(body=event, attempt=next_attempt, error=error)
        return

    await _publish_dlq(body=event, attempt=attempt, error=error)


if __name__ == "__main__":
    asyncio.run(app.run())
