from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from data.models.interaction import Comment
from shared.exceptions import BadRequestError, NotFoundError

class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_comment(self, user_id: int, jamendo_song_id: str, content: str) -> Comment:
        if not content or not content.strip():
            raise BadRequestError("Content cannot be empty")
        
        comment = Comment(
            user_id=user_id, 
            jamendo_song_id=jamendo_song_id, 
            content=content.strip()
        )
        self.db.add(comment)
        try:
            await self.db.commit()
            await self.db.refresh(comment)
            return comment
        except IntegrityError:
            await self.db.rollback()
            raise BadRequestError("Failed to add comment")

    async def remove_comment(self, comment_id: int) -> bool:
        """Xóa comment"""
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(stmt)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise NotFoundError("Comment not found")
        
        await self.db.delete(comment)
        await self.db.commit()
        return True

    async def get_comments_by_song(self, jamendo_song_id: str) -> List[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.jamendo_song_id == jamendo_song_id)
            .options(selectinload(Comment.user))  # Load thông tin user
            .order_by(Comment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_comment(self, comment_id: int, new_content: str) -> Comment:
        if not new_content or not new_content.strip():
            raise BadRequestError("Content cannot be empty")
        
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(stmt)
        comment = result.scalar_one_or_none()
        
        if not comment:
            raise NotFoundError("Comment not found")
        
        comment.content = new_content.strip()
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        stmt = select(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
