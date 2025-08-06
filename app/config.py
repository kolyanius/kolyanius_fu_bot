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
    
    # Validation
    MAX_MESSAGE_LENGTH: int = 200
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def validate(self):
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

config = Config()
