from __future__ import annotations

import asyncio
import logging

from app.services.outbox_publisher import run_publish_batch
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.outbox.publish_outbox_batch")
def publish_outbox_batch() -> int:
    count = asyncio.run(run_publish_batch())
    logger.info("Outbox publish batch finished, count=%s", count)
    return count
