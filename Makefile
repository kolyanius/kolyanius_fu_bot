.PHONY: help build up down restart logs clean rebuild ps shell db-shell

help: ## Показать эту справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Собрать Docker образ
	docker compose build

up: ## Запустить бота
	docker compose up -d
	@echo "✅ Бот запущен! Смотри логи: make logs"

down: ## Остановить бота
	docker compose down

restart: down up ## Перезапустить бота

logs: ## Показать логи бота (следить в реальном времени)
	docker compose logs -f bot

logs-all: ## Показать логи всех сервисов
	docker compose logs -f

ps: ## Показать статус контейнеров
	docker compose ps

rebuild: down ## Пересобрать и запустить (полная пересборка)
	docker compose build --no-cache
	docker compose up -d
	@echo "✅ Бот пересобран и запущен!"

clean: down ## Остановить и удалить volumes (ОСТОРОЖНО: удалит БД!)
	docker compose down -v
	@echo "⚠️  Volumes удалены, база данных очищена"

shell: ## Открыть shell в контейнере бота
	docker compose exec bot sh

db-shell: ## Подключиться к PostgreSQL
	docker compose exec postgres psql -U botuser -d otmazochnik

update: ## Обновить код и перезапустить
	git pull
	docker compose build
	docker compose up -d
	@echo "✅ Код обновлен, бот перезапущен!"

dev: rebuild logs ## Режим разработки: пересборка + логи
