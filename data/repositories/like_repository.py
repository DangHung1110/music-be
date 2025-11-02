from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from data.models.interaction import Like
from sqlalchemy.exc import IntegrityError  
from shared.exceptions import NotFoundError, ConflictRequestError

class LikeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_like(self, user_id: int, jamendo_song_id: str) -> Like:
        if await self.is_liked(user_id, jamendo_song_id):
            raise ConflictRequestError("Already liked this song")
        
        new_like = Like(user_id=user_id, jamendo_song_id=jamendo_song_id)
        self.session.add(new_like)
        try:
            await self.session.commit()
            await self.session.refresh(new_like)
            return new_like
        except IntegrityError:
            await self.session.rollback()
            raise ConflictRequestError("Already liked this song")

    async def remove_like(self, user_id: int, jamendo_song_id: str) -> bool:
        stmt = select(Like).where(
            Like.user_id == user_id, 
            Like.jamendo_song_id == jamendo_song_id
        )
        result = await self.session.execute(stmt)
        like = result.scalar_one_or_none()
        
        if not like:
            raise NotFoundError("Like not found")
        
        await self.session.delete(like)
        await self.session.commit()
        return True

    async def is_liked(self, user_id: int, jamendo_song_id: str) -> bool:
        stmt = select(Like).where(
            Like.user_id == user_id,
            Like.jamendo_song_id == jamendo_song_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_likes_by_user(self, user_id: int) -> List[Like]:
        stmt = (
            select(Like)
            .where(Like.user_id == user_id)
            .options(selectinload(Like.user))  
            .order_by(Like.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_song(self, jamendo_song_id: str) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Like.id)).where(Like.jamendo_song_id == jamendo_song_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_like(self, user_id: int, jamendo_song_id: str) -> Optional[Like]:
        stmt = select(Like).where(
            Like.user_id == user_id,
            Like.jamendo_song_id == jamendo_song_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()