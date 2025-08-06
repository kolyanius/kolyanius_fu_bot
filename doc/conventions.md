# 📋 Соглашения по разработке

> Полное техническое видение см. в @vision.md

---

## 🛠 Утилиты и инструменты

**Обязательный стек:**
- Python 3.11+
- aiogram (Telegram API)  
- openai (клиент для OpenRouter)
- Docker + Docker Compose

**Команды:**
- `docker compose up` (без дефиса)
- `docker compose down`

---

## 🎯 Основные принципы разработки

**KISS превыше всего:**
- Максимальная простота решений
- Никакого оверинжиниринга
- Монолитная архитектура
- Синхронная обработка
- Минимум зависимостей

**Архитектурные ограничения:**
- Один процесс, один контейнер
- Хранение в памяти + файлы
- Polling вместо webhook
- Никаких баз данных

---

## 🎨 Стиль кода

**Python конвенции:**
- PEP 8 стандарт
- Typing hints обязательно
- Dataclasses для конфигурации
- f-strings для форматирования

**Именование:**
```python
# Переменные и функции: snake_case
user_message = "text"
def generate_excuse():

# Константы: UPPER_CASE  
MAX_MESSAGE_LENGTH = 200

# Классы: PascalCase
class Config:
```

---

## 📁 Структура проекта

**Строго следуй структуре из @vision.md раздел 3:**
```
app/
├── main.py              # Точка входа
├── bot.py               # aiogram handlers
├── llm_client.py        # OpenRouter клиент
├── config.py            # Конфигурация
├── prompts.py           # Промпты
└── styles.py            # Стили отмазок
```

**Правила:**
- Один файл = одна ответственность
- Импорты в начале файла
- Никаких вложенных папок в app/

---

## 📦 Работа с зависимостями

**requirements.txt:**
- Только необходимые пакеты
- Закрепленные версии
- Комментарии к назначению

**Пример:**
```
aiogram==3.1.1          # Telegram Bot API
openai==1.3.5           # OpenRouter client  
python-dotenv==1.0.0    # Environment variables
```

---

## ⚠️ Обработка ошибок

**Стратегия из @vision.md раздел 2:**
- Все ошибки логируем
- Пользователю = стандартные сообщения
- 1 retry для LLM API
- Graceful degradation

**Реализация:**
```python
try:
    # operation
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    return "Произошла ошибка, попробуйте еще раз"
```

---

## ⚙️ Конфигурация

**Следуй подходу из @vision.md раздел 10:**
- Dataclass для структуры
- .env для секретов
- Валидация при старте
- Никакой горячей перезагрузки

**Обязательные переменные:**
- `TELEGRAM_BOT_TOKEN` 
- `OPENROUTER_API_KEY`
- `LLM_BASE_URL`

---

## 🧪 Тестирование

**Из @vision.md раздел 2:**
- Только ручное тестирование
- Никаких unit/integration тестов
- Проверка через Docker Compose

**Процедура:**
1. `docker compose up`
2. Отправить `/start` в бот
3. Проверить все стили отмазок
4. Проверить обработку ошибок

---

## 🎮 Команды для проверки

```bash
# Запуск
docker compose up

# Остановка  
docker compose down

# Логи
docker compose logs -f bot

# Проверка конфигурации
python -c "from app.config import config; print('OK')"
```

---

**Принцип:** Если сомневаешься — выбирай более простое решение ✨
