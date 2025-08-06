"""
Основная логика Telegram-бота "Отмазочник"
"""
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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

# Хранение состояний пользователей
user_states = {}

def create_style_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора стилей"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{STYLES['быдло']['emoji']} {STYLES['быдло']['name']}", 
                callback_data="style_быдло"
            ),
            InlineKeyboardButton(
                text=f"{STYLES['корпорат']['emoji']} {STYLES['корпорат']['name']}", 
                callback_data="style_корпорат"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{STYLES['монах']['emoji']} {STYLES['монах']['name']}", 
                callback_data="style_монах"
            ),
            InlineKeyboardButton(
                text=f"{STYLES['инфоцыган']['emoji']} {STYLES['инфоцыган']['name']}", 
                callback_data="style_инфоцыган"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{STYLES['случайный']['emoji']} {STYLES['случайный']['name']}", 
                callback_data="style_случайный"
            )
        ]
    ])
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я бот-отмазочник! 🎭\n\n"
        "Опиши свою ситуацию, и я создам отмазку в выбранном стиле.\n\n"
        f"Максимум {config.MAX_MESSAGE_LENGTH} символов.\n\n"
        "Попробуй написать что-нибудь!"
    )

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    help_text = "🎭 Доступные стили отмазок:\n\n"
    
    for style_key, style_info in STYLES.items():
        if style_key != "случайный":
            help_text += f"{style_info['emoji']} **{style_info['name']}** - {style_info['description']}\n\n"
    
    help_text += f"{STYLES['случайный']['emoji']} **{STYLES['случайный']['name']}** - {STYLES['случайный']['description']}\n\n"
    help_text += "Просто опиши свою ситуацию, и я покажу кнопки для выбора стиля!"
    
    await message.answer(help_text)

@dp.message()
async def message_handler(message: types.Message):
    """Обработчик сообщений - показывает кнопки выбора стиля"""
    # Валидация длины сообщения
    if len(message.text) > config.MAX_MESSAGE_LENGTH:
        await message.answer(
            f"Сообщение слишком длинное! Максимум {config.MAX_MESSAGE_LENGTH} символов.\n"
            f"У тебя {len(message.text)} символов."
        )
        return
    
    # Сохраняем сообщение пользователя
    user_states[message.from_user.id] = {
        "original_message": message.text,
        "message_id": message.message_id
    }
    
    # Показываем кнопки выбора стиля
    keyboard = create_style_keyboard()
    await message.answer(
        "Выбери стиль для отмазки:",
        reply_markup=keyboard
    )

@dp.callback_query()
async def style_callback_handler(callback: types.CallbackQuery):
    """Обработчик нажатий на кнопки стилей"""
    if not callback.data.startswith("style_"):
        await callback.answer("Неизвестная команда")
        return
    
    # Извлекаем выбранный стиль
    selected_style = callback.data.replace("style_", "")
    user_id = callback.from_user.id
    
    # Проверяем есть ли сохраненное сообщение
    if user_id not in user_states:
        await callback.answer("Сначала отправь сообщение с ситуацией!")
        return
    
    original_message = user_states[user_id]["original_message"]
    
    # Обрабатываем случайный стиль
    if selected_style == "случайный":
        available_styles = [s for s in STYLES.keys() if s != "случайный"]
        selected_style = random.choice(available_styles)
    
    # Показываем что бот печатает
    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
    
    # Формируем промпт для выбранного стиля
    prompt = EXCUSE_PROMPTS[selected_style].format(user_message=original_message)
    
    # Генерируем отмазку через LLM
    response = await generate_text(prompt)
    
    # Отправляем отмазку с эмодзи стиля
    style_emoji = STYLES[selected_style]["emoji"]
    style_name = STYLES[selected_style]["name"]
    
    await callback.message.edit_text(
        f"**Стиль: {style_emoji} {style_name}**\n\n{response}"
    )
    
    # Подтверждаем callback
    await callback.answer(f"Отмазка в стиле '{style_name}' готова!")
    
    # Очищаем состояние пользователя
    if user_id in user_states:
        del user_states[user_id]

async def start_bot():
    """Запуск бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)
