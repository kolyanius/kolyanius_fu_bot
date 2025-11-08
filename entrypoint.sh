#!/bin/sh
set -e

echo "🚀 Starting Otmazochnik Bot..."

# Ждем пока PostgreSQL станет доступна
echo "⏳ Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL is ready!"

# Применяем миграции базы данных
echo "🗄️  Running database migrations..."
alembic upgrade head
echo "✅ Migrations applied successfully!"

# Запускаем бота
echo "🤖 Starting bot..."
exec python -m app.main
