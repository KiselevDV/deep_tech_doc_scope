FROM python:3.12-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --only main \
    && rm -rf ~/.cache/pip

COPY . .

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN apt-get update && apt-get install -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"]