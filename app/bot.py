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
logger = logging.getLogger("app")
error_logger = logging.getLogger("error")
request_logger = logging.getLogger("requests")

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
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    try:
        # Логируем входящее сообщение
        request_logger.info(f"MESSAGE | User: {user_id} (@{username}) | Text: '{message.text[:100]}...' | Length: {len(message.text)}")
        
        # Валидация длины сообщения
        if len(message.text) > config.MAX_MESSAGE_LENGTH:
            logger.warning(f"Message too long from user {user_id}: {len(message.text)} chars")
            await message.answer(
                f"Сообщение слишком длинное! Максимум {config.MAX_MESSAGE_LENGTH} символов.\n"
                f"У тебя {len(message.text)} символов."
            )
            return
        
        # Сохраняем сообщение пользователя
        user_states[user_id] = {
            "original_message": message.text,
            "message_id": message.message_id,
            "username": username
        }
        
        # Показываем кнопки выбора стиля
        keyboard = create_style_keyboard()
        await message.answer(
            "Выбери стиль для отмазки:",
            reply_markup=keyboard
        )
        
        logger.info(f"Style selection shown to user {user_id}")
        
    except Exception as e:
        error_logger.error(f"ERROR in message_handler | User: {user_id} | Error: {e}", exc_info=True)
        try:
            await message.answer("Произошла ошибка. Попробуйте еще раз или напишите /start")
        except:
            pass  # Даже ответить не получается

@dp.callback_query()
async def style_callback_handler(callback: types.CallbackQuery):
    """Обработчик нажатий на кнопки стилей"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Unknown"
    
    try:
        if not callback.data.startswith("style_"):
            await callback.answer("Неизвестная команда")
            return
        
        # Извлекаем выбранный стиль
        selected_style = callback.data.replace("style_", "")
        
        # Проверяем есть ли сохраненное сообщение
        if user_id not in user_states:
            await callback.answer("Сначала отправь сообщение с ситуацией!")
            logger.warning(f"No saved message for user {user_id} when selecting style")
            return
        
        original_message = user_states[user_id]["original_message"]
        
        # Обрабатываем случайный стиль
        actual_style = selected_style
        if selected_style == "случайный":
            available_styles = [s for s in STYLES.keys() if s != "случайный"]
            actual_style = random.choice(available_styles)
            logger.info(f"Random style selected for user {user_id}: {actual_style}")
        
        # Логируем выбор стиля
        request_logger.info(f"STYLE_SELECTED | User: {user_id} (@{username}) | Selected: {selected_style} | Actual: {actual_style}")
        
        # Показываем что бот печатает
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
        
        # Формируем промпт для выбранного стиля
        prompt = EXCUSE_PROMPTS[actual_style].format(user_message=original_message)
        
        # Генерируем отмазку через LLM
        response = await generate_text(prompt, user_id=user_id, style=actual_style)
        
        # Отправляем отмазку с эмодзи стиля
        style_emoji = STYLES[actual_style]["emoji"]
        style_name = STYLES[actual_style]["name"]
        
        await callback.message.edit_text(
            f"**Стиль: {style_emoji} {style_name}**\n\n{response}"
        )
        
        # Подтверждаем callback
        await callback.answer(f"Отмазка в стиле '{style_name}' готова!")
        
        # Логируем завершение
        logger.info(f"Excuse generated successfully for user {user_id} in style {actual_style}")
        
        # Очищаем состояние пользователя
        if user_id in user_states:
            del user_states[user_id]
            
    except Exception as e:
        error_logger.error(f"ERROR in style_callback_handler | User: {user_id} | Callback: {callback.data} | Error: {e}", exc_info=True)
        try:
            await callback.answer("Произошла ошибка при генерации отмазки")
            await callback.message.edit_text("❌ Произошла ошибка. Попробуйте еще раз или напишите /start")
        except:
            pass

async def start_bot():
    """Запуск бота"""
    logger.info("🤖 Telegram бот запускается...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        error_logger.error(f"Critical error in bot polling: {e}", exc_info=True)
        raise
