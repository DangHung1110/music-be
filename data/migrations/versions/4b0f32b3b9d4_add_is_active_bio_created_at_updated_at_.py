from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4b0f32b3b9d4'
down_revision = '8ae3dff02576'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'is_active')
