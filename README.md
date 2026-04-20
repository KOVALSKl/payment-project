# Payment project

Асинхронный сервис приёма платежей на `FastAPI` + `PostgreSQL` с паттерном outbox.

## Что реализовано

- API для создания/чтения платежей (`POST /api/v1/payments/`, `GET /api/v1/payments/{id}`);
- авторизация всех API запросов через `X-API-Key`;
- идемпотентность создания платежа через `Idempotency-Key`;
- outbox pattern: запись платежа и outbox-события в одной транзакции;
- периодическая публикация outbox -> `payments.new` через `Celery beat` + `Celery worker`;
- consumer на FastStream для обработки `payments.new`;
- эмуляция шлюза (2-5 секунд, вероятность успеха 90%);
- webhook-уведомление с retry (3 попытки, экспоненциальная задержка);
- DLQ (`payments.dlq`) для сообщений после исчерпания retry;
- первая миграция Alembic для таблиц `payments` и `payment_outbox`.

## Требования

- `Python` 3.11+
- `Poetry` 2.x
- `PostgreSQL` 16+ (локально или через Docker)
- для Docker-запуска: `Docker` + `Docker Compose` v2

## Переменные окружения

```bash
cp .env.example .env
```

Ключевые переменные:

- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` - подключение к PostgreSQL
- `API_KEY` - значение заголовка `X-API-Key`
- `RABBITMQ_URL` - URL RabbitMQ для outbox publisher
- `PAYMENTS_NEW_QUEUE` - имя очереди доменных событий (по умолчанию `payments.new`)
- `PAYMENTS_RETRY_QUEUE` - очередь отложенных retry (`payments.retry`)
- `PAYMENTS_DLQ_QUEUE` - очередь dead-letter (`payments.dlq`)
- `WEBHOOK_MAX_ATTEMPTS` - максимум попыток webhook-доставки (по умолчанию `3`)
- `RETRY_BASE_DELAY_SECONDS` - базовая задержка для backoff
- `CELERY_BROKER_URL` - брокер Celery
- `OUTBOX_PUBLISH_BATCH_SIZE` - размер батча outbox за один проход
- `OUTBOX_BEAT_INTERVAL_SECONDS` - интервал запуска outbox-задачи

## Локальный запуск

1. Установить зависимости:

```bash
poetry install
```

2. Поднять PostgreSQL и создать БД из `.env`.

3. Применить миграции:

```bash
poetry run alembic upgrade head
```

4. Запустить API:

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Запустить Celery worker:

```bash
poetry run celery -A app.workers.celery_app:celery_app worker --loglevel=info
```

6. Запустить Celery beat:

```bash
poetry run celery -A app.workers.celery_app:celery_app beat --loglevel=info
```

7. Запустить FastStream consumer:

```bash
poetry run python -m app.consumers.payment_consumer
```

API: `http://127.0.0.1:8000`, документация: `http://127.0.0.1:8000/docs`.

## Запуск через Docker Compose

```bash
docker compose up --build -d
```

Поднимутся сервисы `db`, `rabbitmq`, `api`, `celery_worker`, `celery_beat`, `consumer`.

После первого старта примените миграции:

```bash
docker compose exec api alembic upgrade head
```

Остановка:

```bash
docker compose down
```

RabbitMQ management UI: `http://127.0.0.1:15672` (по умолчанию `guest/guest`).

## API примеры

Во всех запросах передавайте заголовок `X-API-Key`.

### Создание платежа

`POST /api/v1/payments/` (обязателен `Idempotency-Key`):

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/v1/payments/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_static_api_key" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "amount": "100.50",
    "currency": "RUB",
    "description": "Тестовый платеж",
    "metadata": {"order_id": "123"},
    "webhook_url": "https://example.com/webhook"
  }'
```

Ответ: `202 Accepted`, поля `payment_id`, `status`, `created_at`.

### Получение платежа

`GET /api/v1/payments/{payment_id}`:

```bash
curl -sS "http://127.0.0.1:8000/api/v1/payments/1" \
  -H "X-API-Key: your_static_api_key"
```

В ответе есть `failure_reason` (заполняется при неуспешной эмуляции платежа).

## Test plan (ручной)

1. **Happy path**
   - Создайте платеж с рабочим `webhook_url`.
   - Проверьте, что после обработки `status` становится `succeeded` или `failed`, `processed_at` заполнен.

2. **Retry webhook**
   - Укажите невалидный/недоступный `webhook_url`.
   - Проверьте логи `consumer`: должно быть до 3 попыток с экспоненциальной задержкой.

3. **DLQ**
   - После 3 неудачных попыток проверьте наличие сообщения в очереди `payments.dlq` через RabbitMQ UI (`http://127.0.0.1:15672`).

4. **Idempotent redelivery**
   - Повторно доставьте то же сообщение в `payments.new`.
   - Убедитесь, что бизнес-обработка платежа не выполняется второй раз (повторной установки `processed_at` нет), но webhook-часть повторно пытается доставку.

## Краткая структура проекта

- `app/api/` - HTTP API
- `app/services/payment/` - бизнес-логика создания/чтения платежей
- `app/consumers/` - FastStream consumer обработки `payments.new`
- `app/models/` - SQLAlchemy модели `payments` и `payment_outbox`
- `app/services/outbox_publisher.py` - публикация outbox в RabbitMQ
- `app/messaging/rabbitmq_retry.py` - публикация retry и DLQ сообщений
- `app/workers/` - конфигурация Celery, периодические задачи
- `docker-compose.yml` - контейнерная инфраструктура
