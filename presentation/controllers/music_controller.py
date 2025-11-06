from fastapi import APIRouter, Query
from shared.responses import OK
from business.services.music_service import MusicService
from infrastructure.config.jamendo import JamendoConfig

router = APIRouter(prefix="/music", tags=["Music"])

@router.get("/jamendo-client-id")
async def get_jamendo_client_id():
    """Get Jamendo Client ID for frontend use"""
    return OK(
        message="Jamendo Client ID retrieved successfully",
        metadata={"client_id": JamendoConfig.JAMENDO_CLIENT_ID}
    ).send()

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

