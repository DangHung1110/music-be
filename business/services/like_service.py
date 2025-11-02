from data.repositories.like_repository import LikeRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from data.models.interaction import Like

class LikeService:
    def __init__(self, db: AsyncSession):
        self.repo = LikeRepository(db)

    async def like_song(self, user_id: int, jamendo_song_id: str) -> Like:
        return await self.repo.add_like(user_id, jamendo_song_id)

    async def unlike_song(self, user_id: int, jamendo_song_id: str) -> bool:
        return await self.repo.remove_like(user_id, jamendo_song_id)

    async def toggle_like(self, user_id: int, jamendo_song_id: str) -> Dict[str, Any]:
        is_liked = await self.repo.is_liked(user_id, jamendo_song_id)
        
        if is_liked:
            await self.repo.remove_like(user_id, jamendo_song_id)
            return {
                "liked": False,
                "message": "Unliked successfully"
            }
        else:
            like = await self.repo.add_like(user_id, jamendo_song_id)
            return {
                "liked": True,
                "message": "Liked successfully",
                "like_id": like.id
            }

    async def is_song_liked(self, user_id: int, jamendo_song_id: str) -> bool:
        return await self.repo.is_liked(user_id, jamendo_song_id)

    async def get_user_liked_song_ids(self, user_id: int) -> List[str]:
        likes = await self.repo.get_likes_by_user(user_id)
        return [like.jamendo_song_id for like in likes]

    async def get_song_like_count(self, jamendo_song_id: str) -> int:
        return await self.repo.count_by_song(jamendo_song_id)