"""
Конфигурация для Telegram-бота "Отмазочник"
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # LLM для генерации текста
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://gptunnel.ru/v1")
    MODEL_NAME: str = "gpt-4o"  # Быстрая модель
    MAX_TOKENS: int = 500   # Короткие ответы
    TEMPERATURE: float = 0.7
    RETRY_COUNT: int = 1

    # Whisper API для транскрипции голосовых сообщений
    # По умолчанию использует те же credentials что и LLM
    # Можно указать отдельные, если Whisper на другом сервере
    WHISPER_API_KEY: str = os.getenv("WHISPER_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
    WHISPER_BASE_URL: str = os.getenv("WHISPER_BASE_URL", "https://api.openai.com/v1")  # Стандартный OpenAI endpoint

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://botuser:botpassword@localhost:5432/otmazochnik")

    # Validation
    MAX_MESSAGE_LENGTH: int = 200

    # Logging
    LOG_LEVEL: str = "INFO"

    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required")
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")

config = Config()
