"""
Точка входа для Telegram-бота "Отмазочник"
"""
import asyncio
import logging
import os
from datetime import datetime
from app.config import config
from app.bot import start_bot

def setup_logging():
    """Настройка логирования в файлы"""
    # Создаем папку logs если не существует
    os.makedirs("logs", exist_ok=True)
    
    # Основной логгер приложения
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    
    # Логгер ошибок
    error_logger = logging.getLogger("error")
    error_logger.setLevel(logging.ERROR)
    
    # Логгер запросов пользователей
    request_logger = logging.getLogger("requests")
    request_logger.setLevel(logging.INFO)
    
    # Форматтер для всех логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Хендлер для app.log
    app_handler = logging.FileHandler("logs/app.log", encoding='utf-8')
    app_handler.setFormatter(formatter)
    app_logger.addHandler(app_handler)
    
    # Хендлер для errors.log
    error_handler = logging.FileHandler("logs/errors.log", encoding='utf-8')
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    
    # Хендлер для requests.log
    request_handler = logging.FileHandler("logs/requests.log", encoding='utf-8')
    request_handler.setFormatter(formatter)
    request_logger.addHandler(request_handler)
    
    # Базовый логгер для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().setLevel(config.LOG_LEVEL)

def validate_startup():
    """Расширенная валидация при старте"""
    app_logger = logging.getLogger("app")
    
    try:
        # Валидация конфигурации
        config.validate()
        app_logger.info("✅ Конфигурация валидна")
        
        # Проверка доступности LLM API
        from app.llm_client import get_client
        client = get_client()
        app_logger.info(f"✅ LLM клиент инициализирован: {config.LLM_BASE_URL}")
        app_logger.info(f"✅ Модель: {config.MODEL_NAME}")
        
        # Проверка папки logs
        if os.path.exists("logs"):
            app_logger.info("✅ Папка logs существует")
        else:
            app_logger.warning("⚠️  Папка logs будет создана")
            
        return True
        
    except Exception as e:
        error_logger = logging.getLogger("error")
        error_logger.error(f"❌ Ошибка валидации: {e}", exc_info=True)
        return False

def main():
    """Главная функция запуска бота"""
    # Настройка логирования
    setup_logging()
    app_logger = logging.getLogger("app")
    
    try:
        app_logger.info("🚀 Запуск бота 'Отмазочник'")
        
        # Расширенная валидация
        if not validate_startup():
            app_logger.error("❌ Валидация не прошла, остановка")
            return
            
        app_logger.info("✅ Все проверки пройдены, запуск бота")
        
        # Запуск бота
        asyncio.run(start_bot())
        
    except KeyboardInterrupt:
        app_logger.info("⏹️  Бот остановлен пользователем")
    except Exception as e:
        error_logger = logging.getLogger("error") 
        error_logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        app_logger.info("👋 Завершение работы бота")

if __name__ == "__main__":
    main()
