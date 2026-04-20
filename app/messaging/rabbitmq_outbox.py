"""Синхронная публикация в RabbitMQ (kombu) для вызова из Celery через asyncio.to_thread."""

from __future__ import annotations

from typing import Any

from kombu import Connection, Queue


def publish_outbox_event(
    body: dict[str, Any],
    *,
    rabbitmq_url: str,
    queue_name: str,
) -> None:
    with Connection(rabbitmq_url) as conn:
        with conn.channel() as channel:
            queue = Queue(queue_name, channel=channel, durable=True)
            queue.declare()
            producer = conn.Producer(channel=channel, serializer="json")
            producer.publish(
                body,
                routing_key=queue_name,
                exchange="",
                declare=[queue],
            )
