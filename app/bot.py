"""
Основная логика Telegram-бота "Отмазочник"
"""
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from app.config import config
from app.llm_client import generate_text
from app.prompts import BASIC_PROMPT

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
async def message_handler(message: types.Message):
    """Обработчик сообщений через LLM"""
    # Показываем что бот печатает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Формируем промпт с сообщением пользователя
    prompt = BASIC_PROMPT.format(user_message=message.text)
    
    # Генерируем ответ через LLM
    response = await generate_text(prompt)
    
    # Отправляем ответ пользователю
    await message.answer(response)

async def start_bot():
    """Запуск бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)
