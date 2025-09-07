from fastapi import APIRouter, Query, Body, Depends
from presentation.middleware.auth_middleware import get_current_user
from shared.decorators import async_handler
from typing import Annotated
from shared.responses import OK
from business.services.playlists_service import PlayListService
from infrastructure.config.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
router=APIRouter(prefix="/Playlist",tags=["Playlist"])
@router.get("/search")
@async_handler
async def search_music(query: str = Query(..., description="Search keyword for tracks"),):
    playlist_service=PlayListService()
    results=await playlist_service.search_playlist(query)
    return OK(message="Tracks fetched successfully",metadata={"playlists":results}).send()
@router.post("/create")
@async_handler
async def create_playlist(
     db: Annotated[AsyncSession, Depends(get_db)],
     current_user:dict=Depends(get_current_user),
    title: str = Body(...),
    description: str = Body(...),
    source: str = Body(...),
):
    owner_id = current_user["user_id"]
    playlist_service = PlayListService(db)
    result = await playlist_service.create_playlist(title, owner_id, description, source)
    return OK(message="Playlist created successfully", metadata={"playlist": result}).send()
