"""merge oauth migration

Revision ID: a3bc480b39ea
Revises: 4b0f32b3b9d4, 782ea224f4bc
Create Date: 2025-09-28 13:07:17.346850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3bc480b39ea'
down_revision: Union[str, Sequence[str], None] = ('4b0f32b3b9d4', '782ea224f4bc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
