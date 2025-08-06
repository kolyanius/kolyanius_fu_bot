# 🔧 Техническое видение проекта — Telegram-бот «Отмазочник»

---

## 1. Технологии

**Backend:**
- Python 3.11+
- aiogram (работа с Telegram API)

**LLM:**
- OpenRouter через стандартный openai клиент

**Хранение данных:**
- Текстовые файлы (конфиги, логи)

**Инфраструктура:**
- Docker + Docker Compose

---

## 2. Принципы разработки

**Основные принципы:**
- KISS (Keep It Simple, Stupid) - максимальная простота
- Никакого оверинжиниринга 
- Монолитная архитектура
- Синхронная обработка запросов
- Минимум зависимостей

**Обработка ошибок:**
- Ошибки логируем
- Пользователю возвращаем стандартный ответ "Произошла ошибка"

**Валидация:**
- Максимум 200 символов для ввода пользователя (выносим в переменную)

**Тестирование:**
- Только ручное тестирование

---

## 3. Структура проекта

```
inv-ai-dd-edu/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа, запуск бота
│   ├── bot.py               # aiogram bot логика и handlers
│   ├── llm_client.py        # Работа с OpenRouter
│   ├── config.py            # Конфигурация
│   ├── prompts.py           # Промпты для LLM
│   └── styles.py            # Стили отмазок
├── logs/                    # Логи приложения
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env                     # Переменные окружения
└── README.md
```

---

## 4. Архитектура проекта

```
Telegram → aiogram Polling → Handlers → LLM Client → OpenRouter → Response → User
```

**Компоненты:**
- **aiogram Bot** - основная логика, handlers, polling
- **LLM Client** - формирование промптов и запросы к OpenRouter
- **Styles** - выбор стиля отмазки
- **Config** - централизованная конфигурация

**Поток данных:**
1. Пользователь отправляет сообщение → показываем inline кнопки стилей
2. Пользователь выбирает стиль через callback
3. Валидация исходного сообщения (200 символов)
4. Формирование промпта с учетом выбранного стиля
5. Запрос к OpenRouter
6. Ответ пользователю в Telegram

---

## 5. Модель данных

**В памяти (runtime):**
```python
# Состояние пользователей
user_states = {
    user_id: {
        "original_message": "текст от пользователя",
        "timestamp": datetime
    }
}
```

**В файлах:**
- **Конфигурация** - `.env` файл с переменными
- **Логи** - текстовые файлы в `logs/`
- **Промпты** - Python словари в `prompts.py`
- **Стили** - Python словари в `styles.py`

**Структура стилей:**
```python
STYLES = {
    "быдло": {
        "name": "Быдло", 
        "emoji": "💪"
    },
    "корпорат": {
        "name": "Корпорат", 
        "emoji": "💼"
    },
    "монах": {
        "name": "Монах", 
        "emoji": "🙏"
    },
    "инфоцыган": {
        "name": "Инфоцыган", 
        "emoji": "🔮"
    }
}
```

---

## 6. Работа с LLM

**Провайдер:**
- OpenRouter через стандартный openai клиент

**Конфигурация:**
```python
# config.py
MODEL_NAME = "openai/gpt-4o"
MAX_TOKENS = 150
TEMPERATURE = 0.8
RETRY_COUNT = 1
```

**Структура работы:**
```python
# llm_client.py
import openai

client = openai.OpenAI(
    base_url=LLM_BASE_URL,
    api_key=OPENROUTER_API_KEY
)

def generate_excuse(user_message: str, style: str) -> str:
    prompt = PROMPTS[style].format(user_message=user_message)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE
    )
    return response.choices[0].message.content
```

**Обработка ошибок:**
- 1 retry при падении API
- При неудаче возвращаем стандартную ошибку

---

## 7. Мониторинг

**Логирование:**
- Запросы пользователей (user_id, сообщение, выбранный стиль)
- Ошибки API (время, тип ошибки, user_id)
- Время ответа LLM
- Старт/стоп бота

**Инструменты:**
- Python logging в файлы
- Простые print() для дебага

**Структура логов:**
```
logs/
├── app.log          # Основные события
├── errors.log       # Ошибки
└── requests.log     # Запросы пользователей (с user_id)
```

**Персональные данные:**
- Логируем user_id как есть

---

## 8. Сценарии работы

**Сценарий 1: Первое использование**
1. Пользователь отправляет `/start`
2. Бот отвечает приветствием и инструкцией
3. Пользователь отправляет любое сообщение
4. Бот показывает 5 кнопок: 4 стиля + "Случайный стиль"
5. Пользователь выбирает стиль
6. Бот генерирует и отправляет отмазку

**Сценарий 2: Обычное использование**
1. Пользователь отправляет сообщение с причиной
2. Бот показывает 5 кнопок: 4 стиля + "Случайный стиль"
3. Пользователь выбирает стиль 
4. Бот генерирует и отправляет отмазку

**Сценарий 3: Помощь**
1. Пользователь отправляет `/help`
2. Бот отвечает с описанием всех стилей и примерами

**Сценарий 4: Ошибки**
1. Слишком длинное сообщение (>200 символов) → "Сообщение слишком длинное"
2. Ошибка LLM API → "Произошла ошибка, попробуйте еще раз"
3. Таймаут → "Произошла ошибка, попробуйте еще раз"

**Кнопки:**
- 💪 Быдло
- 💼 Корпорат  
- 🙏 Монах
- 🔮 Инфоцыган
- 🎲 Случайный стиль

---

## 9. Деплой

**Способ деплоя:**
- Docker Compose (команда `docker compose`)
- Один контейнер с ботом
- Polling (без внешних портов)

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

**Переменные окружения (.env):**
```
TELEGRAM_BOT_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
```

**Хостинг:**
- VPS, облако или локальная машина

---

## 10. Подход к конфигурированию

**Структура конфигурации:**
```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # LLM
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    MODEL_NAME: str = "openai/gpt-4o"
    MAX_TOKENS: int = 150
    TEMPERATURE: float = 0.8
    RETRY_COUNT: int = 1
    
    # Validation
    MAX_MESSAGE_LENGTH: int = 200
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required")

config = Config()
config.validate()  # Проверка при старте приложения
```

**Подход:**
- Валидация обязательных переменных при старте
- Изменения через Docker stop/start (без горячей перезагрузки)

---

## 11. Подход к логгированию

**Логгеры:**
```python
# В main.py
import logging
from datetime import datetime

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app_logger = logging.FileHandler('logs/app.log')
error_logger = logging.FileHandler('logs/errors.log') 
requests_logger = logging.FileHandler('logs/requests.log')
```

**Что логируем:**
- **app.log**: старт/стоп бота, общие события
- **errors.log**: все ошибки с трейсбэком
- **requests.log**: user_id, что спросили, выбранный стиль, что ответил бот, время ответа

**Формат requests.log:**
```
2024-01-15 12:30:45 - INFO - User 12345 | Input: "не сделал отчет" | Style: "корпорат" | Output: "В связи с форс-мажорными обстоятельствами..." | Response time: 2.3s
```

**Уровни логов:**
- INFO для обычных событий
- ERROR для ошибок  
- DEBUG отключен

**Чувствительные данные:**
- Логируем полный текст сообщений и ответов для анализа качества

---

## 🎯 Итоговые принципы

1. **Максимальная простота** - KISS превыше всего
2. **Никакого оверинжиниринга** - только необходимое
3. **Один запуск** - docker compose up и все работает
4. **Прозрачность** - все логируется для анализа
5. **Надежность** - graceful обработка ошибок
6. **Масштабируемость** - легко добавить новые стили и функции

Техническое видение готово к реализации! 🚀
