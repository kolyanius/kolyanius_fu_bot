FROM python:3.11-slim

WORKDIR /app

# Установить netcat для проверки доступности PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Установить Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать код приложения
COPY app/ ./app/
COPY logs/ ./logs/

# Скопировать Alembic конфигурацию для миграций
COPY alembic/ ./alembic/
COPY alembic.ini .

# Скопировать и настроить entrypoint скрипт
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Использовать entrypoint для автоматических миграций
ENTRYPOINT ["./entrypoint.sh"]
