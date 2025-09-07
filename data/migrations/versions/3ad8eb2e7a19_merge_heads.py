"""Merge heads

Revision ID: 3ad8eb2e7a19
Revises: 68636183c50c, ca662caf0848
Create Date: 2025-09-05 15:55:53.107255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ad8eb2e7a19'
down_revision: Union[str, Sequence[str], None] = ('68636183c50c', 'ca662caf0848')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
