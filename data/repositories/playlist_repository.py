import httpx
from infrastructure.config.jamendo import JamendoConfig
from data.models.playlist import Playlist
class PlaylistRespository:
    def __init__(self):
        self.JAMENDO_CLIENT_ID=JamendoConfig.JAMENDO_CLIENT_ID
        self.BASE_URL=JamendoConfig.BASE_URL
    async def search_playlists(self,query:str,limit:int=10):
        url=f"{self.BASE_URL}/playlists/tracks"
        params={
            "client_id":self.JAMENDO_CLIENT_ID,
            "format":"json",
            "limit":limit,
            "name":query
        }
        async with httpx.AsyncClient() as client:
            response=await client.get(url,params=params)
            return response.json()
    async def create_playlist(self, title: str, owner_id: int, description: str,source: str):
        new_playlist = Playlist(
            title=title,
            description=description,
            owner_id=owner_id,
            source=source
        )
        return new_playlist
        