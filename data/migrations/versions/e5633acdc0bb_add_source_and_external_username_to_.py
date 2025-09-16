"""add source and external_username to playlists

Revision ID: e5633acdc0bb
Revises: af9a04454ab1
Create Date: 2025-09-05 22:47:30.860957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5633acdc0bb'
down_revision: Union[str, Sequence[str], None] = 'af9a04454ab1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
