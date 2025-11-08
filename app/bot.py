"""
Основная логика Telegram-бота "Отмазочник" v2.0
Новые фичи: feedback, regenerate, history, favorites, voice messages
"""
import asyncio
import logging
import random
import time
import io
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.exceptions import TelegramBadRequest
from app.config import config
from app.llm_client import generate_text
from app.prompts import EXCUSE_PROMPTS
from app.styles import STYLES
from app import database as db

# Настройка логирования
logger = logging.getLogger("app")
error_logger = logging.getLogger("error")
request_logger = logging.getLogger("requests")

# Инициализация бота
bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Хранение временных состояний (для регенерации)
regenerate_cache = {}  # {user_id: {"original_message": str, "style": str}}


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создать главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Новая отмазка", callback_data="menu_new")
        ],
        [
            InlineKeyboardButton(text="📜 История", callback_data="menu_history"),
            InlineKeyboardButton(text="⭐ Избранное", callback_data="menu_favorites")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="menu_help")
        ]
    ])
    return keyboard


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
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
        ]
    ])
    return keyboard


def create_action_keyboard(excuse_id: int, is_fav: bool = False) -> InlineKeyboardMarkup:
    """Создать клавиатуру действий после генерации (feedback, regenerate, favorite)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍", callback_data=f"rate_up_{excuse_id}"),
            InlineKeyboardButton(text="👎", callback_data=f"rate_down_{excuse_id}"),
            InlineKeyboardButton(
                text="⭐ Убрать" if is_fav else "⭐ В избранное",
                callback_data=f"fav_toggle_{excuse_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🔄 Тот же стиль", callback_data="regenerate"),
            InlineKeyboardButton(text="🎨 Другой стиль", callback_data="change_style")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")
        ]
    ])
    return keyboard


# ==================== КОМАНДЫ ====================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Создаем или обновляем пользователя в БД
    await db.get_or_create_user(user_id, username, first_name)

    keyboard = create_main_menu_keyboard()

    await message.answer(
        "🎭 *Привет! Я бот-отмазочник v2.0!*\n\n"
        "*Что я умею:*\n"
        "✅ Генерировать отмазки в 4 стилях\n"
        "✅ Принимать голосовые сообщения\n"
        "✅ Сохранять историю и избранное\n\n"
        "💡 Выбери действие из меню ниже:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    help_text = "🎭 *Доступные стили отмазок:*\n\n"

    for style_key, style_info in STYLES.items():
        if style_key != "случайный":
            help_text += f"{style_info['emoji']} *{style_info['name']}* - {style_info['description']}\n\n"

    help_text += f"{STYLES['случайный']['emoji']} *{STYLES['случайный']['name']}* - {STYLES['случайный']['description']}\n\n"
    help_text += "*Как пользоваться:*\n"
    help_text += "1. Опиши ситуацию текстом или голосом\n"
    help_text += "2. Выбери стиль отмазки\n"
    help_text += "3. Оцени результат 👍/👎\n"
    help_text += "4. Добавь в избранное ⭐\n"
    help_text += "5. Или запроси другой вариант 🔄"

    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("history"))
async def history_handler(message: types.Message):
    """Обработчик команды /history - показывает последние отмазки в пределах лимита"""
    user_id = message.from_user.id

    try:
        # Загружаем больше отмазок, чтобы выбрать те, что влезут
        excuses = await db.get_user_history(user_id, limit=20)

        if not excuses:
            await message.answer(
                "📭 Твоя история пуста!\n\n"
                "Отправь мне ситуацию и я создам первую отмазку."
            )
            return

        # Telegram лимит 4096 символов, оставляем запас
        MAX_LENGTH = 3700
        header = "📜 *Твоя история*\n\n"
        footer = "\n\n💡 Используй /favorites для просмотра избранного"

        response = header
        added_count = 0

        for i, excuse in enumerate(excuses, 1):
            style_emoji = STYLES[excuse.style]['emoji']
            rating_text = ""
            if excuse.rating == 1:
                rating_text = " 👍"
            elif excuse.rating == -1:
                rating_text = " 👎"

            # Формируем текст отмазки БЕЗ сокращения
            situation = excuse.original_message[:100] + ('...' if len(excuse.original_message) > 100 else '')

            excuse_entry = f"{i}. {style_emoji} *{STYLES[excuse.style]['name']}*{rating_text}\n"
            excuse_entry += f"   _Ситуация: {situation}_\n"
            excuse_entry += f"   {excuse.generated_text}\n\n"

            # Проверяем, влезет ли эта отмазка
            if len(response + excuse_entry + footer) > MAX_LENGTH:
                break

            response += excuse_entry
            added_count += 1

        # Показываем сколько отмазок из скольких
        if added_count < len(excuses):
            response += f"\n_Показано {added_count} из {len(excuses)} отмазок_"

        response += footer

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        error_logger.error(f"Error in history_handler for user {user_id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке истории")


@dp.message(Command("favorites"))
async def favorites_handler(message: types.Message):
    """Обработчик команды /favorites - показывает избранные отмазки в пределах лимита"""
    user_id = message.from_user.id

    try:
        favorites = await db.get_user_favorites(user_id, limit=50)

        if not favorites:
            await message.answer(
                "⭐ Избранное пусто!\n\n"
                "После генерации отмазки нажми ⭐ чтобы добавить её в избранное."
            )
            return

        # Telegram лимит 4096 символов, оставляем запас
        MAX_LENGTH = 3700
        header = "⭐ *Твоё избранное*\n\n"

        response = header
        added_count = 0

        for i, excuse in enumerate(favorites, 1):
            style_emoji = STYLES[excuse.style]['emoji']
            situation = excuse.original_message[:100] + ('...' if len(excuse.original_message) > 100 else '')

            # Формируем текст БЕЗ сокращения отмазки
            excuse_entry = f"{i}. {style_emoji} *{STYLES[excuse.style]['name']}*\n"
            excuse_entry += f"   _Ситуация: {situation}_\n"
            excuse_entry += f"   {excuse.generated_text}\n\n"

            # Проверяем, влезет ли эта отмазка
            if len(response + excuse_entry) > MAX_LENGTH:
                break

            response += excuse_entry
            added_count += 1

        # Показываем сколько отмазок из скольких
        if added_count < len(favorites):
            response += f"\n_Показано {added_count} из {len(favorites)} избранных_"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        error_logger.error(f"Error in favorites_handler for user {user_id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке избранного")


@dp.message(Command("stats"))
async def stats_handler(message: types.Message):
    """Обработчик команды /stats - показывает статистику пользователя"""
    user_id = message.from_user.id

    try:
        stats = await db.get_user_stats(user_id)
        user = await db.get_or_create_user(user_id)

        response = "📊 *Твоя статистика:*\n\n"
        response += f"🎭 Всего отмазок: {stats['total_excuses']}\n"
        response += f"⭐ В избранном: {stats['total_favorites']}\n"

        if stats['favorite_style']:
            fav_style = STYLES[stats['favorite_style']]
            response += f"💎 Любимый стиль: {fav_style['emoji']} {fav_style['name']}\n"

        response += f"\n📅 С нами с: {user.created_at.strftime('%d.%m.%Y')}"

        await message.answer(response, parse_mode="Markdown")

    except Exception as e:
        error_logger.error(f"Error in stats_handler for user {user_id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке статистики")


@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    """Обработчик команды /admin <пароль> - показывает статистику администратора"""
    user_id = message.from_user.id

    try:
        # Удаляем сообщение с командой (в нем может быть пароль)
        try:
            await message.delete()
        except:
            pass  # Если не удалось удалить - не критично

        # Парсим команду
        parts = message.text.split(maxsplit=1)

        if len(parts) < 2:
            await message.answer(
                "🔐 *Админ-панель*\n\n"
                "Использование: `/admin <пароль>`\n\n"
                "_Сообщение с паролем будет автоматически удалено_",
                parse_mode="Markdown"
            )
            return

        password = parts[1]

        # Проверяем пароль
        if not config.ADMIN_PASSWORD:
            await message.answer("❌ Админ-пароль не настроен в конфигурации")
            return

        if password != config.ADMIN_PASSWORD:
            logger.warning(f"Failed admin login attempt from user {user_id}")
            await message.answer("❌ Неверный пароль")
            return

        # Получаем статистику
        stats = await db.get_admin_stats()

        # Формируем ответ
        response = "👑 *Админ-панель*\n\n"
        response += "📊 *Общая статистика:*\n\n"
        response += f"👥 Всего пользователей: {stats['total_users']}\n"
        response += f"🎭 Всего отмазок: {stats['total_excuses']}\n"
        response += f"⭐ Всего в избранном: {stats['total_favorites']}\n"

        if stats['avg_response_time']:
            response += f"⚡ Среднее время генерации: {stats['avg_response_time']}с\n"

        if stats['popular_style']:
            pop_style = STYLES[stats['popular_style']]
            response += f"🔥 Популярный стиль: {pop_style['emoji']} {pop_style['name']}\n"

        # Топ пользователей
        if stats['top_users']:
            response += "\n🏆 *Топ-5 пользователей:*\n"
            for i, (uid, username, count) in enumerate(stats['top_users'], 1):
                username_display = f"@{username}" if username else f"ID {uid}"
                response += f"{i}. {username_display} - {count} отмазок\n"

        await message.answer(response, parse_mode="Markdown")
        logger.info(f"Admin panel accessed by user {user_id}")

    except Exception as e:
        error_logger.error(f"Error in admin_handler: {e}", exc_info=True)
        await message.answer("❌ Ошибка при загрузке админ-статистики")


# ==================== ОБРАБОТКА ГОЛОСОВЫХ СООБЩЕНИЙ ====================

@dp.message(F.voice)
async def voice_handler(message: types.Message):
    """Обработчик голосовых сообщений - транскрипция через Whisper API"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    try:
        await message.answer("🎤 Обрабатываю голосовое сообщение...")

        # Скачиваем голосовое сообщение
        voice = message.voice
        file = await bot.get_file(voice.file_id)
        voice_bytes = io.BytesIO()
        await bot.download_file(file.file_path, voice_bytes)
        voice_bytes.seek(0)

        # Транскрибируем через OpenAI Whisper API
        from app.llm_client import get_whisper_client
        whisper_client = get_whisper_client()

        # Создаем файл с правильным расширением
        voice_bytes.name = "voice.ogg"

        # Выполняем транскрипцию в executor (синхронный вызов в async)
        def transcribe():
            return whisper_client.audio.transcriptions.create(
                model=config.WHISPER_MODEL,  # gpt-4o-mini-transcribe по умолчанию
                file=voice_bytes,
                response_format="text",  # Простой текст вместо JSON
                prompt=config.WHISPER_PROMPT  # Промпт для улучшения качества
            )

        transcription = await asyncio.get_event_loop().run_in_executor(None, transcribe)

        # При response_format="text" возвращается просто строка
        transcribed_text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
        logger.info(f"Transcribed voice from user {user_id}: {transcribed_text[:100]}")

        # Валидация длины
        if len(transcribed_text) > config.MAX_MESSAGE_LENGTH:
            await message.answer(
                f"🎤 Распознано: _{transcribed_text[:100]}..._\n\n"
                f"❌ Слишком длинное сообщение! Максимум {config.MAX_MESSAGE_LENGTH} символов.\n"
                f"У тебя {len(transcribed_text)} символов."
            )
            return

        # Сохраняем в кэш для регенерации
        regenerate_cache[user_id] = {"original_message": transcribed_text}

        # Показываем кнопки выбора стиля
        keyboard = create_style_keyboard()
        await message.answer(
            f"🎤 Распознано: _{transcribed_text}_\n\n"
            "Выбери стиль для отмазки:",
            reply_markup=keyboard
        )

        request_logger.info(f"VOICE | User: {user_id} (@{username}) | Text: '{transcribed_text}' | Length: {len(transcribed_text)}")

    except Exception as e:
        error_logger.error(f"Error in voice_handler for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при обработке голосового сообщения.\n"
            "Попробуй отправить текстом или повтори позже."
        )


# ==================== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ====================

@dp.message(F.text)
async def message_handler(message: types.Message):
    """Обработчик текстовых сообщений - показывает кнопки выбора стиля"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    try:
        # Создаем или обновляем пользователя
        await db.get_or_create_user(user_id, username, message.from_user.first_name)

        # Логируем входящее сообщение
        request_logger.info(f"MESSAGE | User: {user_id} (@{username}) | Text: '{message.text[:100]}' | Length: {len(message.text)}")

        # Валидация длины сообщения
        if len(message.text) > config.MAX_MESSAGE_LENGTH:
            logger.warning(f"Message too long from user {user_id}: {len(message.text)} chars")
            await message.answer(
                f"📝 Сообщение слишком длинное! Максимум {config.MAX_MESSAGE_LENGTH} символов.\n"
                f"У тебя {len(message.text)} символов."
            )
            return

        # Сохраняем сообщение для регенерации
        regenerate_cache[user_id] = {"original_message": message.text}

        # Показываем кнопки выбора стиля
        keyboard = create_style_keyboard()
        await message.answer(
            "🎨 Выбери стиль для отмазки:",
            reply_markup=keyboard
        )

        logger.info(f"Style selection shown to user {user_id}")

    except Exception as e:
        error_logger.error(f"ERROR in message_handler | User: {user_id} | Error: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка. Попробуй еще раз или напиши /start")


# ==================== ОБРАБОТКА CALLBACK КНОПОК ====================

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    try:
        keyboard = create_main_menu_keyboard()

        await callback.message.edit_text(
            "🎭 *Главное меню*\n\n"
            "💡 Выбери действие из меню ниже:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        error_logger.error(f"Error in back_to_menu_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка")


@dp.callback_query(F.data == "menu_new")
async def menu_new_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'Новая отмазка'"""
    try:
        await callback.message.edit_text(
            "📝 *Создать новую отмазку*\n\n"
            f"Опиши свою ситуацию текстом (макс {config.MAX_MESSAGE_LENGTH} символов) "
            "или отправь голосовое сообщение.\n\n"
            "После этого я предложу тебе выбрать стиль отмазки! 🎨",
            parse_mode="Markdown"
        )
        await callback.answer()
    except Exception as e:
        error_logger.error(f"Error in menu_new_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка")


@dp.callback_query(F.data == "menu_history")
async def menu_history_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'История'"""
    user_id = callback.from_user.id

    try:
        excuses = await db.get_user_history(user_id, limit=20)

        if not excuses:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
            ])
            await callback.message.edit_text(
                "📭 *Твоя история пуста!*\n\n"
                "Отправь мне ситуацию и я создам первую отмазку.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Telegram лимит 4096 символов, оставляем запас
        MAX_LENGTH = 3700
        header = "📜 *Твоя история*\n\n"
        footer = "\n\n💡 Используй /favorites для просмотра избранного"

        response = header
        added_count = 0

        for i, excuse in enumerate(excuses, 1):
            style_emoji = STYLES[excuse.style]['emoji']
            rating_text = ""
            if excuse.rating == 1:
                rating_text = " 👍"
            elif excuse.rating == -1:
                rating_text = " 👎"

            situation = excuse.original_message[:100] + ('...' if len(excuse.original_message) > 100 else '')

            # Формируем текст БЕЗ сокращения отмазки
            excuse_entry = f"{i}. {style_emoji} *{STYLES[excuse.style]['name']}*{rating_text}\n"
            excuse_entry += f"   _Ситуация: {situation}_\n"
            excuse_entry += f"   {excuse.generated_text}\n\n"

            # Проверяем, влезет ли эта отмазка
            if len(response + excuse_entry + footer) > MAX_LENGTH:
                break

            response += excuse_entry
            added_count += 1

        # Показываем сколько отмазок из скольких
        if added_count < len(excuses):
            response += f"\n_Показано {added_count} из {len(excuses)} отмазок_"

        response += footer

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
        ])

        await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        error_logger.error(f"Error in menu_history_handler for user {user_id}: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке истории")


@dp.callback_query(F.data == "menu_favorites")
async def menu_favorites_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'Избранное'"""
    user_id = callback.from_user.id

    try:
        favorites = await db.get_user_favorites(user_id, limit=50)

        if not favorites:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
            ])
            await callback.message.edit_text(
                "⭐ *Избранное пусто!*\n\n"
                "После генерации отмазки нажми ⭐ чтобы добавить её в избранное.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Telegram лимит 4096 символов, оставляем запас
        MAX_LENGTH = 3700
        header = "⭐ *Твоё избранное*\n\n"

        response = header
        added_count = 0

        for i, excuse in enumerate(favorites, 1):
            style_emoji = STYLES[excuse.style]['emoji']
            situation = excuse.original_message[:100] + ('...' if len(excuse.original_message) > 100 else '')

            # Формируем текст БЕЗ сокращения отмазки
            excuse_entry = f"{i}. {style_emoji} *{STYLES[excuse.style]['name']}*\n"
            excuse_entry += f"   _Ситуация: {situation}_\n"
            excuse_entry += f"   {excuse.generated_text}\n\n"

            # Проверяем, влезет ли эта отмазка
            if len(response + excuse_entry) > MAX_LENGTH:
                break

            response += excuse_entry
            added_count += 1

        # Показываем сколько отмазок из скольких
        if added_count < len(favorites):
            response += f"\n_Показано {added_count} из {len(favorites)} избранных_"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
        ])

        await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        error_logger.error(f"Error in menu_favorites_handler for user {user_id}: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке избранного")


@dp.callback_query(F.data == "menu_stats")
async def menu_stats_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'Статистика'"""
    user_id = callback.from_user.id

    try:
        stats = await db.get_user_stats(user_id)
        user = await db.get_or_create_user(user_id)

        response = "📊 *Твоя статистика:*\n\n"
        response += f"🎭 Всего отмазок: {stats['total_excuses']}\n"
        response += f"⭐ В избранном: {stats['total_favorites']}\n"

        if stats['favorite_style']:
            fav_style = STYLES[stats['favorite_style']]
            response += f"💎 Любимый стиль: {fav_style['emoji']} {fav_style['name']}\n"

        response += f"\n📅 С нами с: {user.created_at.strftime('%d.%m.%Y')}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
        ])

        await callback.message.edit_text(response, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        error_logger.error(f"Error in menu_stats_handler for user {user_id}: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке статистики")


@dp.callback_query(F.data == "menu_help")
async def menu_help_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 'Помощь'"""
    try:
        help_text = "🎭 *Доступные стили отмазок:*\n\n"

        for style_key, style_info in STYLES.items():
            if style_key != "случайный":
                help_text += f"{style_info['emoji']} *{style_info['name']}* - {style_info['description']}\n\n"

        help_text += f"{STYLES['случайный']['emoji']} *{STYLES['случайный']['name']}* - {STYLES['случайный']['description']}\n\n"
        help_text += "*Как пользоваться:*\n"
        help_text += "1. Опиши ситуацию текстом или голосом\n"
        help_text += "2. Выбери стиль отмазки\n"
        help_text += "3. Оцени результат 👍/👎\n"
        help_text += "4. Добавь в избранное ⭐\n"
        help_text += "5. Или запроси другой вариант 🔄"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
        ])

        await callback.message.edit_text(help_text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        error_logger.error(f"Error in menu_help_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка")


@dp.callback_query(F.data.startswith("style_"))
async def style_callback_handler(callback: types.CallbackQuery):
    """Обработчик нажатий на кнопки стилей - генерирует отмазку"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Unknown"

    try:
        # Извлекаем выбранный стиль
        selected_style = callback.data.replace("style_", "")

        # Проверяем есть ли сохраненное сообщение
        if user_id not in regenerate_cache:
            await callback.answer("❌ Сначала отправь сообщение с ситуацией!")
            logger.warning(f"No cached message for user {user_id} when selecting style")
            return

        original_message = regenerate_cache[user_id]["original_message"]

        # Обрабатываем случайный стиль
        actual_style = selected_style
        if selected_style == "случайный":
            available_styles = [s for s in STYLES.keys() if s != "случайный"]
            actual_style = random.choice(available_styles)
            logger.info(f"Random style selected for user {user_id}: {actual_style}")

        # Сохраняем стиль для регенерации
        regenerate_cache[user_id]["style"] = actual_style

        # Логируем выбор стиля
        request_logger.info(f"STYLE_SELECTED | User: {user_id} (@{username}) | Selected: {selected_style} | Actual: {actual_style}")

        # Показываем что бот печатает
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

        # Формируем промпт для выбранного стиля
        prompt = EXCUSE_PROMPTS[actual_style].format(user_message=original_message)

        # Генерируем отмазку через LLM
        start_time = time.time()
        response = await generate_text(prompt, user_id=user_id, style=actual_style)
        response_time = time.time() - start_time

        # Сохраняем в БД
        excuse = await db.create_excuse(
            user_id=user_id,
            original_message=original_message,
            style=actual_style,
            generated_text=response,
            response_time=response_time
        )

        # Проверяем, в избранном ли
        is_fav = await db.is_favorite(user_id, excuse.id)

        # Отправляем отмазку с кнопками действий
        style_emoji = STYLES[actual_style]["emoji"]
        style_name = STYLES[actual_style]["name"]

        keyboard = create_action_keyboard(excuse.id, is_fav)

        await callback.message.edit_text(
            f"*Стиль: {style_emoji} {style_name}*\n\n{response}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        # Подтверждаем callback
        await callback.answer(f"✅ Отмазка готова!")

        # Логируем завершение
        logger.info(f"Excuse {excuse.id} generated for user {user_id} in style {actual_style}")

    except Exception as e:
        error_logger.error(f"ERROR in style_callback_handler | User: {user_id} | Error: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при генерации отмазки")
        try:
            await callback.message.edit_text("❌ Произошла ошибка. Попробуй еще раз или напиши /start")
        except:
            pass


@dp.callback_query(F.data.startswith("rate_"))
async def rating_callback_handler(callback: types.CallbackQuery):
    """Обработчик оценок 👍/👎"""
    user_id = callback.from_user.id

    try:
        # Парсим данные: rate_up_123 или rate_down_123
        parts = callback.data.split("_")
        action = parts[1]  # up или down
        excuse_id = int(parts[2])

        rating = 1 if action == "up" else -1

        # Обновляем рейтинг в БД
        await db.update_excuse_rating(excuse_id, rating)

        # Обновляем клавиатуру
        is_fav = await db.is_favorite(user_id, excuse_id)
        keyboard = create_action_keyboard(excuse_id, is_fav)

        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except TelegramBadRequest as e:
            # Игнорируем ошибку "message is not modified" (когда пользователь нажал ту же кнопку повторно)
            if "message is not modified" not in str(e):
                raise

        emoji = "👍" if rating == 1 else "👎"
        await callback.answer(f"{emoji} Спасибо за оценку!")

        logger.info(f"User {user_id} rated excuse {excuse_id}: {rating}")

    except Exception as e:
        error_logger.error(f"Error in rating_callback_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при сохранении оценки")


@dp.callback_query(F.data.startswith("fav_toggle_"))
async def favorite_toggle_handler(callback: types.CallbackQuery):
    """Обработчик добавления/удаления из избранного"""
    user_id = callback.from_user.id

    try:
        # Парсим данные: fav_toggle_123
        excuse_id = int(callback.data.split("_")[2])

        # Проверяем текущий статус
        is_fav = await db.is_favorite(user_id, excuse_id)

        if is_fav:
            # Удаляем из избранного
            await db.remove_from_favorites(user_id, excuse_id)
            await callback.answer("⭐ Удалено из избранного")
            logger.info(f"User {user_id} removed excuse {excuse_id} from favorites")
        else:
            # Добавляем в избранное
            await db.add_to_favorites(user_id, excuse_id)
            await callback.answer("⭐ Добавлено в избранное!")
            logger.info(f"User {user_id} added excuse {excuse_id} to favorites")

        # Обновляем клавиатуру
        keyboard = create_action_keyboard(excuse_id, not is_fav)

        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except TelegramBadRequest as e:
            # Игнорируем ошибку "message is not modified"
            if "message is not modified" not in str(e):
                raise

    except Exception as e:
        error_logger.error(f"Error in favorite_toggle_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при работе с избранным")


@dp.callback_query(F.data == "change_style")
async def change_style_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 🎨 Другой стиль - показывает выбор стилей"""
    user_id = callback.from_user.id

    try:
        # Проверяем есть ли кэшированные данные
        if user_id not in regenerate_cache or "original_message" not in regenerate_cache[user_id]:
            await callback.answer("❌ Данные не найдены. Отправь новое сообщение.")
            return

        original_message = regenerate_cache[user_id]["original_message"]

        # Показываем кнопки выбора стиля
        keyboard = create_style_keyboard()

        await callback.message.edit_text(
            f"📝 Твоя ситуация: _{original_message[:100]}{'...' if len(original_message) > 100 else ''}_\n\n"
            "🎨 Выбери новый стиль для отмазки:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer("🎨 Выбери стиль")

        logger.info(f"User {user_id} requested style change")

    except Exception as e:
        error_logger.error(f"Error in change_style_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка")


@dp.callback_query(F.data == "regenerate")
async def regenerate_handler(callback: types.CallbackQuery):
    """Обработчик кнопки 🔄 Другой вариант - регенерирует отмазку"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "Unknown"

    try:
        # Проверяем есть ли кэшированные данные
        if user_id not in regenerate_cache or "style" not in regenerate_cache[user_id]:
            await callback.answer("❌ Данные для регенерации не найдены. Отправь новое сообщение.")
            return

        original_message = regenerate_cache[user_id]["original_message"]
        style = regenerate_cache[user_id]["style"]

        # Показываем что бот печатает
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")
        await callback.answer("🔄 Генерирую новый вариант...")

        # Формируем промпт
        prompt = EXCUSE_PROMPTS[style].format(user_message=original_message)

        # Генерируем новую отмазку
        start_time = time.time()
        response = await generate_text(prompt, user_id=user_id, style=style)
        response_time = time.time() - start_time

        # Сохраняем в БД
        excuse = await db.create_excuse(
            user_id=user_id,
            original_message=original_message,
            style=style,
            generated_text=response,
            response_time=response_time
        )

        # Проверяем избранное
        is_fav = await db.is_favorite(user_id, excuse.id)

        # Отправляем новую отмазку
        style_emoji = STYLES[style]["emoji"]
        style_name = STYLES[style]["name"]

        keyboard = create_action_keyboard(excuse.id, is_fav)

        await callback.message.edit_text(
            f"*Стиль: {style_emoji} {style_name}* 🔄\n\n{response}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        request_logger.info(f"REGENERATE | User: {user_id} (@{username}) | Style: {style} | Excuse: {excuse.id}")
        logger.info(f"Regenerated excuse {excuse.id} for user {user_id}")

    except Exception as e:
        error_logger.error(f"Error in regenerate_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при регенерации")


# ==================== ЗАПУСК БОТА ====================

async def start_bot():
    """Запуск бота"""
    logger.info("🤖 Telegram бот запускается...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        error_logger.error(f"Critical error in bot polling: {e}", exc_info=True)
        raise
