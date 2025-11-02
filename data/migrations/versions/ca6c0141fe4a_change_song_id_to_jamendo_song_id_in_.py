"""Change song_id to jamendo_song_id in likes and comments

Revision ID: ca6c0141fe4a
Revises: 99b4f0713358
Create Date: 2025-11-01
"""
from alembic import op
import sqlalchemy as sa


revision = 'ca6c0141fe4a'
down_revision = '99b4f0713358'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # === Sửa bảng likes ===
    if 'likes' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('likes')]
        
        # ✅ Chỉ thêm nếu chưa có jamendo_song_id
        if 'jamendo_song_id' not in columns and 'song_id' in columns:
            # 1. Drop foreign key nếu có
            constraints = inspector.get_foreign_keys('likes')
            for constraint in constraints:
                if 'song_id' in constraint.get('constrained_columns', []):
                    op.drop_constraint(constraint['name'], 'likes', type_='foreignkey')
            
            # 2. Drop index cũ
            indexes = inspector.get_indexes('likes')
            for index in indexes:
                if 'song_id' in index.get('column_names', []):
                    op.drop_index(index['name'], table_name='likes')
            
            # 3. Thêm column mới
            op.add_column('likes', sa.Column('jamendo_song_id', sa.String(length=50), nullable=True))
            
            # 4. Copy data (nếu có)
            op.execute("UPDATE likes SET jamendo_song_id = CAST(song_id AS CHAR) WHERE song_id IS NOT NULL")
            
            # 5. Set NOT NULL
            op.alter_column('likes', 'jamendo_song_id',
                          existing_type=sa.String(length=50),
                          nullable=False)
            
            # 6. Drop column cũ
            op.drop_column('likes', 'song_id')
        
        # ✅ Nếu đã có jamendo_song_id nhưng vẫn còn song_id → chỉ xóa song_id
        elif 'jamendo_song_id' in columns and 'song_id' in columns:
            # Drop foreign key và index
            constraints = inspector.get_foreign_keys('likes')
            for constraint in constraints:
                if 'song_id' in constraint.get('constrained_columns', []):
                    op.drop_constraint(constraint['name'], 'likes', type_='foreignkey')
            
            indexes = inspector.get_indexes('likes')
            for index in indexes:
                if 'song_id' in index.get('column_names', []):
                    op.drop_index(index['name'], table_name='likes')
            
            # Xóa song_id
            op.drop_column('likes', 'song_id')
        
        # ✅ Tạo index mới (nếu chưa có)
        indexes = inspector.get_indexes('likes')
        index_names = [idx['name'] for idx in indexes]
        if 'idx_user_jamendo_song' not in index_names:
            op.create_index('idx_user_jamendo_song', 'likes', ['user_id', 'jamendo_song_id'], unique=True)
    
    # === Sửa bảng comments ===
    if 'comments' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('comments')]
        
        # ✅ Chỉ thêm nếu chưa có jamendo_song_id
        if 'jamendo_song_id' not in columns and 'song_id' in columns:
            # 1. Drop foreign key nếu có
            constraints = inspector.get_foreign_keys('comments')
            for constraint in constraints:
                if 'song_id' in constraint.get('constrained_columns', []):
                    op.drop_constraint(constraint['name'], 'comments', type_='foreignkey')
            
            # 2. Drop index cũ
            indexes = inspector.get_indexes('comments')
            for index in indexes:
                if 'song_id' in index.get('column_names', []):
                    op.drop_index(index['name'], table_name='comments')
            
            # 3. Thêm column mới
            op.add_column('comments', sa.Column('jamendo_song_id', sa.String(length=50), nullable=True))
            
            # 4. Copy data
            op.execute("UPDATE comments SET jamendo_song_id = CAST(song_id AS CHAR) WHERE song_id IS NOT NULL")
            
            # 5. Set NOT NULL
            op.alter_column('comments', 'jamendo_song_id',
                          existing_type=sa.String(length=50),
                          nullable=False)
            
            # 6. Drop column cũ
            op.drop_column('comments', 'song_id')
        
        # ✅ Nếu đã có jamendo_song_id nhưng vẫn còn song_id
        elif 'jamendo_song_id' in columns and 'song_id' in columns:
            constraints = inspector.get_foreign_keys('comments')
            for constraint in constraints:
                if 'song_id' in constraint.get('constrained_columns', []):
                    op.drop_constraint(constraint['name'], 'comments', type_='foreignkey')
            
            indexes = inspector.get_indexes('comments')
            for index in indexes:
                if 'song_id' in index.get('column_names', []):
                    op.drop_index(index['name'], table_name='comments')
            
            op.drop_column('comments', 'song_id')
        
        # ✅ Tạo index mới (nếu chưa có)
        indexes = inspector.get_indexes('comments')
        index_names = [idx['name'] for idx in indexes]
        if 'idx_comments_jamendo_song' not in index_names:
            op.create_index('idx_comments_jamendo_song', 'comments', ['jamendo_song_id'])


def downgrade() -> None:
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # === Rollback comments ===
    if 'comments' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('comments')]
        
        if 'jamendo_song_id' in columns:
            indexes = inspector.get_indexes('comments')
            for index in indexes:
                if index['name'] == 'idx_comments_jamendo_song':
                    op.drop_index(index['name'], table_name='comments')
            
            if 'song_id' not in columns:
                op.add_column('comments', sa.Column('song_id', sa.Integer(), nullable=True))
                op.execute("UPDATE comments SET song_id = CAST(jamendo_song_id AS UNSIGNED) WHERE jamendo_song_id IS NOT NULL")
                op.alter_column('comments', 'song_id',
                               existing_type=sa.Integer(),
                               nullable=False)
            
            op.drop_column('comments', 'jamendo_song_id')
    
    # === Rollback likes ===
    if 'likes' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('likes')]
        
        if 'jamendo_song_id' in columns:
            indexes = inspector.get_indexes('likes')
            for index in indexes:
                if index['name'] == 'idx_user_jamendo_song':
                    op.drop_index(index['name'], table_name='likes')
            
            if 'song_id' not in columns:
                op.add_column('likes', sa.Column('song_id', sa.Integer(), nullable=True))
                op.execute("UPDATE likes SET song_id = CAST(jamendo_song_id AS UNSIGNED) WHERE jamendo_song_id IS NOT NULL")
                op.alter_column('likes', 'song_id',
                               existing_type=sa.Integer(),
                               nullable=False)
            
            op.drop_column('likes', 'jamendo_song_id')
