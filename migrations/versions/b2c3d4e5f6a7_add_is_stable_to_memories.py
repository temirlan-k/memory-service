"""add is_stable to memories

Revision ID: b2c3d4e5f6a7
Revises: cd362cd2e8e7
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'cd362cd2e8e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('memories', sa.Column('is_stable', sa.Boolean(), nullable=False, server_default='true'))
    op.create_index('ix_memories_is_stable', 'memories', ['is_stable'])


def downgrade() -> None:
    op.drop_index('ix_memories_is_stable', table_name='memories')
    op.drop_column('memories', 'is_stable')
