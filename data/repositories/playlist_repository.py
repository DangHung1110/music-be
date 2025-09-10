import httpx
from fastapi import HTTPException, Request
from sqlalchemy import insert, select
from sqlalchemy.orm import selectinload

from data.models.music import Album, Artist, Song
from data.models.playlist import Playlist, playlist_song_table
from infrastructure.config.jamendo import JamendoConfig


class PlaylistRespository:
    def __init__(self, db):
        self.db = db
        self.JAMENDO_CLIENT_ID = JamendoConfig.JAMENDO_CLIENT_ID
        self.BASE_URL = JamendoConfig.BASE_URL

    async def search_playlist_jamendo(self, query: str, limit: int = 10):
        url = f"{self.BASE_URL}/playlists/tracks"
        params = {
            "client_id": self.JAMENDO_CLIENT_ID,
            "format": "json",
            "limit": limit,
            "name": query,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json()

    async def search_playlists_local(self, query: str):
        stmt = (
              select(Playlist)
              .options(selectinload(Playlist.songs).selectinload(Song.artist))
              .options(selectinload(Playlist.songs).selectinload(Song.album))
              .where(Playlist.title.ilike(f"%{query}%"))
               )
        result = await self.db.execute(stmt)
        playlists = result.scalars().unique().all() 
        return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "owner_id": p.owner_id,
            "source": p.source,
            "created_at": str(p.created_at),
            "tracks": [
                {
                    "id": s.id,
                    "title": s.title,
                    "duration": s.duration,
                    "file_url": s.file_url,
                    "cover_url": s.cover_url,
                    "jamendo_id": s.jamendo_id,
                    "artist_id":s.artist_id,
                    "album": {
                        "id": s.album.id if s.album else None,
                        "title": s.album.title if s.album else None,
                    },
                }
                for s in p.songs
            ],
        }
        for p in playlists
    ]

    async def create_playlist(
        self, title: str, owner_id: int, description: str, source: str
    ):
        new_playlist = Playlist(
            title=title, description=description, owner_id=owner_id, source=source
        )
        self.db.add(new_playlist)
        await self.db.commit()
        await self.db.refresh(new_playlist)

        # ✅ Trả về dict thay vì object
        return {
            "id": new_playlist.id,
            "title": new_playlist.title,
            "description": new_playlist.description,
            "owner_id": new_playlist.owner_id,
            "source": new_playlist.source,
            "created_at": str(new_playlist.created_at),
        }
    async def save_music_to_playlist(self, playlist_id: int, owner_id: int, song_data: dict):
         stmt_playlist = select(Playlist).where(Playlist.id == playlist_id)
         result = await self.db.execute(stmt_playlist)
         playlist = result.scalar_one_or_none()
         if playlist is None:
            raise HTTPException(status_code=404, detail="Playlist not found")
         if playlist.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="You are not the owner of this playlist")
         artist_id = int(song_data.get("artist_id"))
         artist_name = song_data.get("artist_name")
         stmt_artist = select(Artist).where(Artist.id == artist_id)
         result = await self.db.execute(stmt_artist)
         artist = result.scalar_one_or_none()
         if artist is None:
            artist = Artist(id=artist_id, name=artist_name)
            self.db.add(artist)
            await self.db.flush()

         album_id = int(song_data.get("album_id"))
         album_title = song_data.get("album_name")

         stmt_album = select(Album).where(Album.id == album_id)
         result = await self.db.execute(stmt_album)
         album = result.scalar_one_or_none()
         if album is None:
            album = Album(id=album_id, title=album_title, artist_id=artist_id)
            self.db.add(album)
            await self.db.flush()

   
         stmt_check = select(Song).where(Song.jamendo_id == str(song_data.get("id")))
         result = await self.db.execute(stmt_check)
         song = result.scalar_one_or_none()
         if song is not None:
            raise HTTPException(status_code=400, detail="Song already exists in playlist")
         if song is None:
            song = Song(
               title=song_data.get("name"),
               duration=song_data.get("duration"),
               file_url=song_data.get("audio"),
               cover_url=song_data.get("album_image"),
               jamendo_id=str(song_data.get("id")),
               artist_id=artist_id,
               album_id=album_id,)
            self.db.add(song)
            await self.db.flush()
         stmt_link = playlist_song_table.insert().values(
         playlist_id=playlist_id,
         song_id=song.id)
         await self.db.execute(stmt_link)
         await self.db.commit()
         return {
        "playlist_id": playlist_id,
        "song_id": song.id,
        "status": "saved"}

   
  




