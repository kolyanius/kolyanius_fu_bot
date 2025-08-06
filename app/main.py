"""
Точка входа для Telegram-бота "Отмазочник"
"""
import asyncio
import logging
from app.config import config
from app.bot import start_bot

def main():
    """Главная функция запуска бота"""
    try:
        # Валидация конфигурации
        config.validate()
        
        # Запуск бота
        asyncio.run(start_bot())
        
    except Exception as e:
        logging.error(f"Ошибка запуска бота: {e}")
        raise

if __name__ == "__main__":
    main()
