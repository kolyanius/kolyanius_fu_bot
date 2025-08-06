"""
Основная логика Telegram-бота "Отмазочник"
"""
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from app.config import config

# Настройка логирования
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    await message.answer("Привет! Я бот-отмазочник!")

@dp.message()
async def echo_handler(message: types.Message):
    """Эхо-обработчик - отвечает 'Привет!' на любое сообщение"""
    await message.answer("Привет!")

async def start_bot():
    """Запуск бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)
