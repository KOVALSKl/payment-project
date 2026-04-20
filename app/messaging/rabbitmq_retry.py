"""Утилиты для retry и DLQ публикаций из consumer."""

from __future__ import annotations

from typing import Any

from kombu import Connection, Queue


def _retry_headers(
    *,
    attempt: int,
    error: str | None,
    original_queue: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {
        "x-attempt": attempt,
        "x-original-queue": original_queue,
    }
    if error:
        headers["x-last-error"] = error
    return headers


def publish_retry_event(
    body: dict[str, Any],
    *,
    rabbitmq_url: str,
    main_queue: str,
    retry_queue: str,
    delay_seconds: int,
    attempt: int,
    error: str | None,
) -> None:
    with Connection(rabbitmq_url) as conn:
        with conn.channel() as channel:
            queue = Queue(
                retry_queue,
                channel=channel,
                durable=True,
                queue_arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": main_queue,
                },
            )
            queue.declare()
            producer = conn.Producer(channel=channel, serializer="json")
            producer.publish(
                body,
                routing_key=retry_queue,
                exchange="",
                declare=[queue],
                headers=_retry_headers(
                    attempt=attempt,
                    error=error,
                    original_queue=main_queue,
                ),
                expiration=str(delay_seconds * 1000),
            )


def publish_dlq_event(
    body: dict[str, Any],
    *,
    rabbitmq_url: str,
    dlq_queue: str,
    attempt: int,
    error: str | None,
    original_queue: str,
) -> None:
    with Connection(rabbitmq_url) as conn:
        with conn.channel() as channel:
            queue = Queue(dlq_queue, channel=channel, durable=True)
            queue.declare()
            producer = conn.Producer(channel=channel, serializer="json")
            producer.publish(
                body,
                routing_key=dlq_queue,
                exchange="",
                declare=[queue],
                headers=_retry_headers(
                    attempt=attempt,
                    error=error,
                    original_queue=original_queue,
                ),
            )
