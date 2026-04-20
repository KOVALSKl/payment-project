import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(
                os.path.dirname(
                    (os.path.dirname(os.path.abspath(__file__)))
                ),
            ),
             ".env"), 
        env_file_encoding="utf-8",
        extra="ignore"
    )

class DBConfig(BaseConfig):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class AppConfig(BaseConfig):
    API_KEY: str


class RabbitMQConfig(BaseConfig):
    """Публикация доменных событий (очередь payments.new). Отдельно от транспорта Celery."""

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672//"
    PAYMENTS_NEW_QUEUE: str = "payments.new"
    PAYMENTS_RETRY_QUEUE: str = "payments.retry"
    PAYMENTS_DLQ_QUEUE: str = "payments.dlq"
    WEBHOOK_MAX_ATTEMPTS: int = 3
    RETRY_BASE_DELAY_SECONDS: int = 5


class OutboxPublisherConfig(BaseConfig):
    OUTBOX_PUBLISH_BATCH_SIZE: int = 100
    OUTBOX_BEAT_INTERVAL_SECONDS: int = 15


class CeleryConfig(BaseConfig):
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"


db_config = DBConfig()
app_config = AppConfig()
rabbitmq_config = RabbitMQConfig()
outbox_publisher_config = OutboxPublisherConfig()
celery_config = CeleryConfig()
