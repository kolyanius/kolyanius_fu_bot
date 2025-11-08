"""
Database models для Telegram-бота "Отмазочник"
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Text, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class для всех моделей"""
    pass


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Настройки пользователя
    default_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)

    # Отношения
    excuses: Mapped[list["Excuse"]] = relationship("Excuse", back_populates="user", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"


class Excuse(Base):
    """Модель сгенерированной отмазки"""
    __tablename__ = "excuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))

    # Данные запроса
    original_message: Mapped[str] = mapped_column(Text)
    style: Mapped[str] = mapped_column(String(50))

    # Сгенерированный результат
    generated_text: Mapped[str] = mapped_column(Text)

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1 для 👍, -1 для 👎

    # Дополнительная информация
    response_time: Mapped[Optional[float]] = mapped_column(nullable=True)  # Время генерации в секундах

    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="excuses")
    favorites: Mapped[list["Favorite"]] = relationship("Favorite", back_populates="excuse", cascade="all, delete-orphan")

    # Индексы для быстрого поиска
    __table_args__ = (
        Index('ix_excuses_user_created', 'user_id', 'created_at'),
        Index('ix_excuses_style', 'style'),
    )

    def __repr__(self):
        return f"<Excuse(id={self.id}, user_id={self.user_id}, style={self.style})>"


class Favorite(Base):
    """Модель избранных отмазок"""
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    excuse_id: Mapped[int] = mapped_column(Integer, ForeignKey("excuses.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Отношения
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    excuse: Mapped["Excuse"] = relationship("Excuse", back_populates="favorites")

    # Индексы
    __table_args__ = (
        Index('ix_favorites_user', 'user_id'),
        Index('ix_favorites_unique', 'user_id', 'excuse_id', unique=True),
    )

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, excuse_id={self.excuse_id})>"
