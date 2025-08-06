# 🎭 Telegram-бот "Отмазочник"

Генерирует креативные отмазки в разных стилях с помощью LLM.

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# 1. Создайте .env файл из шаблона
cp env.example .env

# 2. Отредактируйте .env файл:
# TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
# OPENROUTER_API_KEY=ваш_ключ_от_openrouter
# LLM_BASE_URL=https://gptunnel.ru/v1
```

### 2. Получение токенов

**Telegram бот:**
1. Напишите @BotFather в Telegram
2. Создайте бота командой `/newbot`
3. Скопируйте токен в .env файл

**OpenRouter API:**
1. Зарегистрируйтесь на https://openrouter.ai
2. Получите API ключ
3. Или используйте gptunnel.ru

### 3. Запуск

```bash
# Запуск в Docker (рекомендуется)
docker compose up

# Или запуск для разработки
docker compose up --build

# Просмотр логов
docker compose logs -f bot
```

## 🎨 Доступные стили

- **💪 Быдло** - Грубоватые, прямолинейные отмазки с жаргоном
- **💼 Корпорат** - Деловые, бюрократические отмазки в офисном стиле  
- **🙏 Монах** - Философские, мудрые отмазки с духовным подтекстом
- **🔮 Инфоцыган** - Мистические, эзотерические отмазки с магией
- **🎲 Случайный стиль** - Случайный выбор из всех стилей

## 📱 Как пользоваться

1. Запустите бота командой `/start`
2. Опишите свою ситуацию (макс 200 символов)
3. Выберите стиль из предложенных кнопок
4. Получите креативную отмазку!

**Команды:**
- `/start` - Начать работу с ботом
- `/help` - Описание всех стилей

## 🔧 Настройка

### Переменные окружения (.env)

```bash
# Обязательные
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Опциональные  
LLM_BASE_URL=https://gptunnel.ru/v1    # URL LLM провайдера
LOG_LEVEL=INFO                          # Уровень логирования
```

### Конфигурация (app/config.py)

- `MODEL_NAME` - Модель LLM (по умолчанию: gpt-4o)
- `MAX_TOKENS` - Максимум токенов ответа (по умолчанию: 100)
- `TEMPERATURE` - Креативность ответов (по умолчанию: 0.7)
- `MAX_MESSAGE_LENGTH` - Лимит длины сообщений (по умолчанию: 200)

## 📊 Мониторинг

### Логи

Логи сохраняются в папку `logs/`:

- `logs/app.log` - Общие события бота
- `logs/errors.log` - Ошибки с трейсбэками
- `logs/requests.log` - Статистика запросов пользователей

### Просмотр логов

```bash
# В реальном времени
docker compose logs -f bot

# Файлы логов
tail -f logs/app.log
tail -f logs/errors.log  
tail -f logs/requests.log
```

## 🏗️ Архитектура

```
app/
├── main.py           # Точка входа, настройка логирования
├── bot.py            # Telegram handlers, inline кнопки
├── llm_client.py     # LLM API, retry логика
├── config.py         # Конфигурация, валидация
├── prompts.py        # Промпты для разных стилей
└── styles.py         # Определения стилей отмазок
```

**Технологии:**
- Python 3.11+
- aiogram (Telegram Bot API)
- OpenAI client (для OpenRouter)
- Docker + Docker Compose

## 🐛 Диагностика

### Проблемы с запуском

```bash
# Проверить конфигурацию
python test_llm.py

# Проверить логи
docker compose logs bot

# Пересобрать контейнер
docker compose up --build
```

### Типичные ошибки

- **TELEGRAM_BOT_TOKEN is required** - Не указан токен бота в .env
- **OPENROUTER_API_KEY is required** - Не указан API ключ в .env
- **LLM request timeout** - Медленно отвечает LLM провайдер
- **Rate limit exceeded** - Превышен лимит запросов к API

## 📈 Масштабирование

### Производительность
- Retry логика с экспоненциальной задержкой
- Fallback ответы при недоступности LLM
- Таймауты для быстрого ответа пользователям

### Мониторинг
- Детальное логирование всех операций
- Статистика по пользователям и стилям
- Отслеживание времени ответа LLM

## 👨‍💻 Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск для разработки
python -m app.main

# Тестирование LLM
python test_llm.py
```

## 📄 Лицензия

Проект создан для образовательных целей.

---

**🎭 Бот готов генерировать креативные отмазки!**