from fastapi import APIRouter, Query
from shared.responses import OK
from business.services.music_service import MusicService

router = APIRouter(prefix="/music", tags=["Music"])

@router.get("/search")
async def search_music(query: str = Query(...)):
    try:
        music_service = MusicService()
        results = await music_service.smart_search(query)
        return OK(
            message="Tracks fetched successfully",
            metadata=results
        ).send()
    except Exception as e:
        import traceback
        traceback.print_exc()  # 👈 In lỗi ra console
        return {"error": str(e)}

