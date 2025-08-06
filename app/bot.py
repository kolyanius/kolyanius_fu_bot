"""
Основная логика Telegram-бота "Отмазочник"
"""
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from app.config import config
from app.llm_client import generate_text
from app.prompts import BASIC_PROMPT, EXCUSE_PROMPTS
from app.styles import STYLES

# Настройка логирования
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    style_info = STYLES["быдло"]
    await message.answer(
        f"Привет! Я бот-отмазочник! 💪\n\n"
        f"Опиши свою ситуацию, и я создам отмазку в стиле \"{style_info['name']}\".\n"
        f"Максимум {config.MAX_MESSAGE_LENGTH} символов."
    )

@dp.message()
async def message_handler(message: types.Message):
    """Обработчик сообщений - генерация отмазок в стиле 'быдло'"""
    # Валидация длины сообщения
    if len(message.text) > config.MAX_MESSAGE_LENGTH:
        await message.answer(
            f"Сообщение слишком длинное! Максимум {config.MAX_MESSAGE_LENGTH} символов.\n"
            f"У тебя {len(message.text)} символов."
        )
        return
    
    # Показываем что бот печатает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Формируем промпт для генерации отмазки в стиле "быдло"
    prompt = EXCUSE_PROMPTS["быдло"].format(user_message=message.text)
    
    # Генерируем отмазку через LLM
    response = await generate_text(prompt)
    
    # Отправляем отмазку пользователю
    await message.answer(f"💪 {response}")

async def start_bot():
    """Запуск бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)
