"""Initial tables

Revision ID: 001
Revises:
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_active', sa.DateTime(), nullable=False),
        sa.Column('default_style', sa.String(length=50), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create excuses table
    op.create_table(
        'excuses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('original_message', sa.Text(), nullable=False),
        sa.Column('style', sa.String(length=50), nullable=False),
        sa.Column('generated_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE')
    )
    op.create_index('ix_excuses_created_at', 'excuses', ['created_at'])
    op.create_index('ix_excuses_user_created', 'excuses', ['user_id', 'created_at'])
    op.create_index('ix_excuses_style', 'excuses', ['style'])

    # Create favorites table
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('excuse_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['excuse_id'], ['excuses.id'], ondelete='CASCADE')
    )
    op.create_index('ix_favorites_user', 'favorites', ['user_id'])
    op.create_index('ix_favorites_unique', 'favorites', ['user_id', 'excuse_id'], unique=True)


def downgrade() -> None:
    op.drop_table('favorites')
    op.drop_table('excuses')
    op.drop_table('users')
