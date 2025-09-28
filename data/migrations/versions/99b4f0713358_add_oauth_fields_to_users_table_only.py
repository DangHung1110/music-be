"""Add OAuth fields to users table only

Revision ID: 99b4f0713358
Revises: a3bc480b39ea
Create Date: 2025-09-28 13:07:38.696718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99b4f0713358'
down_revision: Union[str, Sequence[str], None] = 'a3bc480b39ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add OAuth fields to users table
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_provider_id', sa.String(length=100), nullable=True))
    
    # Make password nullable for OAuth users
    op.alter_column('users', 'password', nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove OAuth fields
    op.drop_column('users', 'oauth_provider_id')
    op.drop_column('users', 'oauth_provider')
    op.drop_column('users', 'is_verified')
    
    # Make password not nullable again
    op.alter_column('users', 'password', nullable=False)
