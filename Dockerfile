# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder

ENV POETRY_VERSION=2.3.4 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" && poetry config virtualenvs.create ${POETRY_VIRTUALENVS_CREATE}

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-ansi

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
