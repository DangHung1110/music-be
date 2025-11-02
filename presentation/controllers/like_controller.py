from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from business.services.like_service import LikeService
from infrastructure.config.database import get_db
from presentation.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/likes", tags=["Likes"])

def get_like_service(db: AsyncSession = Depends(get_db)):
    return LikeService(db)

@router.post("/songs/{jamendo_song_id}", status_code=201)
async def like_song(
    jamendo_song_id: str,  
    current_user=Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    try:
        like = await service.like_song(current_user.id, jamendo_song_id)
        return {"success": True, "like_id": like.id, "message": "Liked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/songs/{jamendo_song_id}", status_code=204)
async def unlike_song(
    jamendo_song_id: str,
    current_user=Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    try:
        await service.unlike_song(current_user.id, jamendo_song_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/songs/{jamendo_song_id}/toggle", status_code=200)
async def toggle_like(
    jamendo_song_id: str,
    current_user=Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    try:
        result = await service.toggle_like(current_user.id, jamendo_song_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/songs/{jamendo_song_id}/is-liked")
async def is_song_liked(
    jamendo_song_id: str,
    current_user=Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    is_liked = await service.is_song_liked(current_user.id, jamendo_song_id)
    return {"is_liked": is_liked}

@router.get("/me/song-ids")
async def get_my_liked_song_ids(
    current_user=Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
):
    song_ids = await service.get_user_liked_song_ids(current_user.id)
    return {"song_ids": song_ids, "total": len(song_ids)}

@router.get("/songs/{jamendo_song_id}/count")
async def get_like_count(
    jamendo_song_id: str,
    service: LikeService = Depends(get_like_service),
):
    count = await service.get_song_like_count(jamendo_song_id)
    return {"count": count}
