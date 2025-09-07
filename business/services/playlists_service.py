from data.repositories.playlist_repository import  PlaylistRespository
class PlayListService:
    def __init__(self):
        self.repo=PlaylistRespository()
    async def search_playlist(self,query:str):
        playlists=await self.repo.search_playlists(query)
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
    async def create_playlist(self,title:str,owner_id:int,description:str,source:str):
        playlist=await self.repo.create_playlist(title,owner_id,description,source)
        return playlist
        

           