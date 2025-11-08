"""
Database service layer для работы с PostgreSQL
"""
import logging
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.models import Base, User, Excuse, Favorite
from app.config import config

logger = logging.getLogger(__name__)

# Глобальные переменные для engine и session maker
engine = None
async_session_maker = None


async def init_database():
    """Инициализация базы данных"""
    global engine, async_session_maker

    logger.info(f"Initializing database: {config.DATABASE_URL}")

    # Создаем async engine
    engine = create_async_engine(
        config.DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

    # Создаем session maker
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Создаем таблицы (для первого запуска, если миграции не выполнены)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_database():
    """Закрытие соединения с БД"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


@asynccontextmanager
async def get_session():
    """Получить сессию БД"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ==================== USER OPERATIONS ====================

async def get_or_create_user(user_id: int, username: str = None, first_name: str = None) -> User:
    """Получить или создать пользователя"""
    async with get_session() as session:
        # Проверяем существует ли пользователь
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Обновляем last_active и данные профиля
            user.last_active = datetime.utcnow()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            logger.debug(f"Updated user {user_id}")
        else:
            # Создаем нового пользователя
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            logger.info(f"Created new user {user_id}")

        return user


async def update_user_settings(user_id: int, default_style: str = None, is_premium: bool = None):
    """Обновить настройки пользователя"""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            if default_style is not None:
                user.default_style = default_style
            if is_premium is not None:
                user.is_premium = is_premium
            logger.info(f"Updated settings for user {user_id}")


# ==================== EXCUSE OPERATIONS ====================

async def create_excuse(
    user_id: int,
    original_message: str,
    style: str,
    generated_text: str,
    response_time: float = None
) -> Excuse:
    """Создать новую отмазку"""
    async with get_session() as session:
        excuse = Excuse(
            user_id=user_id,
            original_message=original_message,
            style=style,
            generated_text=generated_text,
            response_time=response_time
        )
        session.add(excuse)
        await session.flush()  # Получаем ID
        await session.refresh(excuse)

        logger.info(f"Created excuse {excuse.id} for user {user_id}")
        return excuse


async def get_user_history(user_id: int, limit: int = 10) -> List[Excuse]:
    """Получить историю отмазок пользователя"""
    async with get_session() as session:
        result = await session.execute(
            select(Excuse)
            .where(Excuse.user_id == user_id)
            .order_by(desc(Excuse.created_at))
            .limit(limit)
        )
        excuses = result.scalars().all()
        logger.debug(f"Retrieved {len(excuses)} excuses for user {user_id}")
        return list(excuses)


async def get_excuse_by_id(excuse_id: int) -> Optional[Excuse]:
    """Получить отмазку по ID"""
    async with get_session() as session:
        result = await session.execute(
            select(Excuse).where(Excuse.id == excuse_id)
        )
        return result.scalar_one_or_none()


async def update_excuse_rating(excuse_id: int, rating: int):
    """Обновить рейтинг отмазки (1 для 👍, -1 для 👎)"""
    async with get_session() as session:
        result = await session.execute(
            select(Excuse).where(Excuse.id == excuse_id)
        )
        excuse = result.scalar_one_or_none()

        if excuse:
            excuse.rating = rating
            logger.info(f"Updated rating for excuse {excuse_id}: {rating}")


# ==================== FAVORITE OPERATIONS ====================

async def add_to_favorites(user_id: int, excuse_id: int) -> bool:
    """Добавить отмазку в избранное"""
    async with get_session() as session:
        # Проверяем, не добавлена ли уже
        result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id, Favorite.excuse_id == excuse_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.debug(f"Excuse {excuse_id} already in favorites for user {user_id}")
            return False

        # Добавляем в избранное
        favorite = Favorite(user_id=user_id, excuse_id=excuse_id)
        session.add(favorite)
        logger.info(f"Added excuse {excuse_id} to favorites for user {user_id}")
        return True


async def remove_from_favorites(user_id: int, excuse_id: int) -> bool:
    """Удалить отмазку из избранного"""
    async with get_session() as session:
        result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id, Favorite.excuse_id == excuse_id)
        )
        favorite = result.scalar_one_or_none()

        if favorite:
            await session.delete(favorite)
            logger.info(f"Removed excuse {excuse_id} from favorites for user {user_id}")
            return True

        return False


async def get_user_favorites(user_id: int, limit: int = 20) -> List[Excuse]:
    """Получить избранные отмазки пользователя"""
    async with get_session() as session:
        result = await session.execute(
            select(Excuse)
            .join(Favorite, Favorite.excuse_id == Excuse.id)
            .where(Favorite.user_id == user_id)
            .order_by(desc(Favorite.created_at))
            .limit(limit)
        )
        excuses = result.scalars().all()
        logger.debug(f"Retrieved {len(excuses)} favorites for user {user_id}")
        return list(excuses)


async def is_favorite(user_id: int, excuse_id: int) -> bool:
    """Проверить, находится ли отмазка в избранном"""
    async with get_session() as session:
        result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id, Favorite.excuse_id == excuse_id)
        )
        return result.scalar_one_or_none() is not None


# ==================== ANALYTICS ====================

async def get_user_stats(user_id: int) -> dict:
    """Получить статистику пользователя"""
    async with get_session() as session:
        # Количество всего отмазок
        total_result = await session.execute(
            select(func.count(Excuse.id))
            .where(Excuse.user_id == user_id)
        )
        total_excuses = total_result.scalar()

        # Количество избранных
        favorites_result = await session.execute(
            select(func.count(Favorite.id))
            .where(Favorite.user_id == user_id)
        )
        total_favorites = favorites_result.scalar()

        # Самый популярный стиль
        style_result = await session.execute(
            select(Excuse.style, func.count(Excuse.id).label('count'))
            .where(Excuse.user_id == user_id)
            .group_by(Excuse.style)
            .order_by(desc('count'))
            .limit(1)
        )
        favorite_style_row = style_result.first()
        favorite_style = favorite_style_row[0] if favorite_style_row else None

        return {
            "total_excuses": total_excuses,
            "total_favorites": total_favorites,
            "favorite_style": favorite_style
        }
