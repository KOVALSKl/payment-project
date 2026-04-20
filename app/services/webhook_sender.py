from __future__ import annotations

import httpx


class WebhookDeliveryError(RuntimeError):
    pass


async def send_webhook(url: str, payload: dict) -> None:
    timeout = httpx.Timeout(10.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise WebhookDeliveryError(
            f"Webhook returned bad status code: {response.status_code}"
        )
