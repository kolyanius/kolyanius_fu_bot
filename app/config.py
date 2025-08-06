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
    
    # LLM
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    MODEL_NAME: str = "openai/gpt-4o-mini"  # Быстрая модель
    MAX_TOKENS: int = 100   # Короткие ответы
    TEMPERATURE: float = 0.7
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
