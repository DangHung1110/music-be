from data.repositories.comment_repository import CommentRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from data.models.interaction import Comment

class CommentService:
    def __init__(self, db: AsyncSession):
        self.repo = CommentRepository(db)

    async def add_comment(self, user_id: int, jamendo_song_id: str, content: str) -> Comment:
        return await self.repo.add_comment(user_id, jamendo_song_id, content)

    async def remove_comment(self, comment_id: int, user_id: int) -> bool:
        comment = await self.repo.get_comment_by_id(comment_id)
        if not comment:
            from shared.exceptions import NotFoundError
            raise NotFoundError("Comment not found")
        
        if comment.user_id != user_id:
            from shared.exceptions import BadRequestError
            raise BadRequestError("You can only delete your own comments")
        
        return await self.repo.remove_comment(comment_id)

    async def get_comments_by_song(self, jamendo_song_id: str) -> List[Dict[str, Any]]:
        comments = await self.repo.get_comments_by_song(jamendo_song_id)
        return [comment.to_dict() for comment in comments]

    async def update_comment(self, comment_id: int, user_id: int, new_content: str) -> Comment:
        comment = await self.repo.get_comment_by_id(comment_id)
        if not comment:
            from shared.exceptions import NotFoundError
            raise NotFoundError("Comment not found")
        
        if comment.user_id != user_id:
            from shared.exceptions import BadRequestError
            raise BadRequestError("You can only edit your own comments")
        
        return await self.repo.update_comment(comment_id, new_content)