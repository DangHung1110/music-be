from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from business.services.comment_service import CommentService
from infrastructure.config.database import get_db
from presentation.middleware.auth_middleware import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/comments", tags=["Comments"])

class CommentCreate(BaseModel):
    content: str

class CommentUpdate(BaseModel):
    content: str

def get_comment_service(db: AsyncSession = Depends(get_db)):
    return CommentService(db)

@router.post("/songs/{jamendo_song_id}", status_code=201)
async def add_comment(
    jamendo_song_id: str,  
    data: CommentCreate = Body(...),
    current_user=Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    """Thêm comment cho bài hát"""
    comment = await service.add_comment(current_user.get("user_id"), jamendo_song_id, data.content)
    return comment.to_dict()

@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: int,
    current_user=Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    await service.remove_comment(comment_id, current_user.get("user_id"))

@router.get("/songs/{jamendo_song_id}")
async def get_comments(
    jamendo_song_id: str,
    service: CommentService = Depends(get_comment_service),
):
    comments = await service.get_comments_by_song(jamendo_song_id)
    return {"items": comments, "total": len(comments)}

@router.put("/{comment_id}")
async def update_comment(
    comment_id: int,
    data: CommentUpdate = Body(...),
    current_user=Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
):
    comment = await service.update_comment(comment_id, current_user.get("user_id"), data.content)
    return comment.to_dict()
