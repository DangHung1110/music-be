from data.repositories.music_repository import MusicRespository
from collections import defaultdict

class MusicService:
    def __init__(self):
        self.repo = MusicRespository()

    async def smart_search(self, query: str):

        tracks_json = await self.repo.search_tracks(query)
        tracks = self._format_results_tracks(tracks_json)

        if len(tracks) > 0:
            return {
                "search_type": "track",
                "tracks": tracks
            }

        artist_json = await self.repo.search_by_artist(query)
        artist_data = self._format_results_artist(artist_json)

        return {
            "search_type": "artist",
            "artists": artist_data
        }

    def _format_results_tracks(self, tracks_json):
        results = tracks_json.get("results", [])
        if not results:
            return []

        formatted = []
        for track in results:
            formatted.append({
                "jamendo_id": track.get("id"),
                "title": track.get("name"),
                "duration": track.get("duration"),
                "file_url": track.get("audiodownload"),
                "cover_url": track.get("album_image"),
                "audio": track.get("audio"),
                "artist_name": track.get("artist_name"),
                "artist_id": track.get("artist_id"),
            })
        return formatted

    def _format_results_artist(self, tracks_json):
        results = tracks_json.get("results", [])
        if not results:
            return []

        artists_map = defaultdict(lambda: {
            "artist_id": None,
            "artist_name": None,
            "artist_website": None,
            "artist_image": None,
            "tracks": []
        })

        for track in results:
            aid = track.get("artist_id")
            if not aid:
                continue

            artist = artists_map[aid]
            artist["artist_id"] = aid
            artist["artist_name"] = track.get("artist_name")
            artist["artist_website"] = track.get("artist_website")
            artist["artist_image"] = track.get("artist_image")

            artist["tracks"].append({
                "jamendo_id": track.get("id"),
                "title": track.get("name"),
                "duration": track.get("duration"),
                "file_url": track.get("audiodownload"),
                "cover_url": track.get("album_image"),
                "audio": track.get("audio")
            })

        return list(artists_map.values())
