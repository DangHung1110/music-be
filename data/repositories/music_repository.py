import httpx
from infrastructure.config.jamendo import JamendoConfig

class MusicRespository:
    def __init__(self):
        self.JAMENDO_CLIENT_ID = JamendoConfig.JAMENDO_CLIENT_ID
        self.BASE_URL = JamendoConfig.BASE_URL

    async def search_tracks(self, query: str, limit: int = 10):
        url = f"{self.BASE_URL}/tracks"
        params = {
            "client_id": self.JAMENDO_CLIENT_ID,
            "format": "json",
            "limit": limit,
            "name": query
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json()

    async def search_by_artist(self, artist_name: str, limit: int = 50):
        url = f"{self.BASE_URL}/tracks"
        params = {
            "client_id": self.JAMENDO_CLIENT_ID,
            "format": "json",
            "limit": limit,
            "artist_name": artist_name
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json()
