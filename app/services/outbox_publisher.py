"""Одна итерация: батч pending outbox → RabbitMQ → статус PROCESSED и published_at."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.config import outbox_publisher_config, rabbitmq_config
from app.db.base import async_session_maker
from app.messaging.rabbitmq_outbox import publish_outbox_event
from app.models.enums import OutboxStatus
from app.repositories.payment.outbox_payment import OutboxPaymentRepository


async def run_publish_batch() -> int:
    limit = outbox_publisher_config.OUTBOX_PUBLISH_BATCH_SIZE
    async with async_session_maker() as session:
        async with session.begin():
            repo = OutboxPaymentRepository(session)
            rows = list(await repo.claim_pending_batch(limit))
            if not rows:
                return 0
            for row in rows:
                body = {
                    "event_type": row.event_type,
                    "payload": row.payload,
                    "idempotency_key": row.idempotency_key,
                    "payment_id": row.payment_id,
                }
                await asyncio.to_thread(
                    publish_outbox_event,
                    body,
                    rabbitmq_url=rabbitmq_config.RABBITMQ_URL,
                    queue_name=rabbitmq_config.PAYMENTS_NEW_QUEUE,
                )
                row.status = OutboxStatus.PROCESSED
                row.published_at = datetime.now(timezone.utc)
            return len(rows)
