"""set_role_default_to_user

Revision ID: 782ea224f4bc
Revises: e0bbd556af98
Create Date: 2025-09-28 19:11:24.298429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '782ea224f4bc'
down_revision: Union[str, Sequence[str], None] = 'e0bbd556af98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Set default value for role column to 'user'
    op.alter_column('users', 'role', 
                   existing_type=sa.String(length=50),
                   nullable=True,
                   server_default='user')


def downgrade() -> None:
    """Downgrade schema."""
    # Remove default value for role column
    op.alter_column('users', 'role',
                   existing_type=sa.String(length=50),
                   nullable=True,
                   server_default=None)
