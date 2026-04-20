from datetime import timedelta

from celery import Celery

from app.core.config import celery_config, outbox_publisher_config

celery_app = Celery(
    "payment_project",
    broker=celery_config.CELERY_BROKER_URL,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "publish-outbox-batch": {
            "task": "app.workers.tasks.outbox.publish_outbox_batch",
            "schedule": timedelta(
                seconds=outbox_publisher_config.OUTBOX_BEAT_INTERVAL_SECONDS
            ),
        },
    },
)

import app.workers.tasks.outbox  # noqa: E402, F401
