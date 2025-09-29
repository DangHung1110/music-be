from data.repositories.playlist_repository import  PlaylistRespository
class PlayListService:
    def __init__(self, db):
        self.repo = PlaylistRespository(db)
    async def get_playlists_by_owner(self, owner_id: int):
        
        playlists = await self.repo.get_playlists_by_owner(owner_id)
        return playlists
    """async def search_playlist_local(self, query: str):
        playlists = await self.repo.search_playlists_local(query)
        return playlists
    async def search_playlist_jamendo(self,query:str):
        playlists = await self.repo.search_playlist_jamendo(query)

        results=[]
        for playlist in playlists.get("results",[]):
            tracks=[]
            for track in playlist.get("tracks",[]):
                tracks.append({ 
                  "jamendo_id": track.get("id"),
                  "title": track.get("name"),
                  "duration": track.get("duration"),
                  "file_url": track.get("audiodownload"),
                  "cover_url": track.get("album_image"),
                  "artist_id": track.get("artist_id"),
                  "artist_name":track.get("artist_name"),
                  "audio": track.get("audio")
                })
            results.append({
                "id": playlist.get("id"),
                "owner_id":playlist.get("user_id"),
                "title": playlist.get("name"),
                "user_name":playlist.get("user_name"),
                "created_at":playlist.get("creationdate"),
                "tracks": tracks

            })
        return results
    async def search_playlists_all(self, query: str):
        local = await self.search_playlist_local(query)
        jamendo = await self.search_playlist_jamendo(query)
        return local + jamendo"""
    async def create_playlist(self,title:str,owner_id:int,description:str,source:str):
        playlist=await self.repo.create_playlist(title,owner_id,description,source)
        return playlist
    async def save_music_to_playlist(self, playlist_id: int, owner_id: int, song_data: dict):
        result = await self.repo.save_music_to_playlist(playlist_id, owner_id, song_data)
        return result
    async def remove_song(self, playlist_id: int, song_id: int, owner_id: int):
        return await self.repo.remove_song_from_playlist(playlist_id, song_id, owner_id)
    async def delete_playlist(self, playlist_id: int, owner_id: int):
        return await self.repo.delete_playlist(playlist_id, owner_id)
    async def get_songs_in_playlist(self, playlist_id: int, owner_id: int):
        songs = await self.repo.get_songs_in_playlist(playlist_id, owner_id)
        return songs
           