from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import asyncio
import random
import json


class SimplifiedSpotifyTrack:
    def __init__(self, track_data, requester):
        self.title = track_data["name"]
        self.length = track_data["duration_ms"]
        self.main_artist = track_data["artists"][0]["name"]
        self.desc = f"{self.main_artist} - {self.title}"
        self.url = track_data["external_urls"]["spotify"]
        self.requester = requester


class SpotifyTrack(SimplifiedSpotifyTrack):
    def __init__(self, track_data, requester):
        super().__init__(track_data, requester)
        self.id = track_data["id"]
        self.image = track_data["album"]["images"][0]["url"]
        self.artists = list()
        for a in track_data["artists"]:
            artist_obj = {"name": a["name"], "id": a["id"], "url": a["external_urls"]["spotify"]}
            self.artists.append(artist_obj)
        self.explicit = track_data["explicit"]
        self.url = track_data["external_urls"]["spotify"]
        self.uri = track_data["uri"]


class InvalidLink(Exception):
    """Simple Exception that carries the error message"""
    def __init__(self, message):
        self.message = message


class Spotify:
    def __init__(self, spotify_credentials):
        client_id = spotify_credentials["client_id"]
        client_secret = spotify_credentials["client_secret"]
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.client = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def playlist_data(self, playlist_id):
        playlist_fields = "id, images, name, owner.display_name, tracks.total"
        try:
            playlist_data = self.client.playlist(playlist_id, fields=playlist_fields)
        except Exception as e:
            print(f"[ERR][Music] Error while getting playlist data: {e}")
            playlist_data = None
        return playlist_data

    def track_data(self, track_id):
        try:
            track_data = self.client.track(track_id)
        except Exception as e:
            print(f"[ERR][Music] Error while getting track data: {e}")
            track_data = None
        return track_data

    def playlist_tracks(self, playlist_id, limit, requester):
        if limit > 600:
            limit = 600

        fields = (
            "items.track.artists.name, items.track.artists.id, items.track.duration_ms, items.track.explicit,"
            "items.track.name, items.track.uri, items.track.external_urls.spotify"
        )
        playlist_tracks = list()
        for index in range(0, limit, 100):
            tracks_on_page = self.client.playlist_items(playlist_id, fields=fields, offset=index)["items"]
            for track_data in tracks_on_page:
                track_data = track_data["track"]
                track = SimplifiedSpotifyTrack(track_data, requester)
                playlist_tracks.append(track)
        return playlist_tracks

    # @staticmethod
    # def link_info(link):
    #     fields = link.split(":")
    #     if len(fields) >= 3:
    #         return SpotifyLink(fields[-2], fields[-1])
    #     fields = link.split("/")
    #     if len(fields) >= 3:
    #         return SpotifyLink(fields[-2], fields[-1].split("?")[0])
    #     return SpotifyLink()

    # def validate_link_for_play(self, author_input):
    #     link = self.link_info(author_input)
    #     if link.type in ["playlist", "track"]:
    #         return link
    #     return None

    def prepare_tracks_for_youtube(self, valid_spotify_link, requester):
        regex_groups = valid_spotify_link.groups()
        spot_id = regex_groups[3]
        playlist = regex_groups[1] == "playlist"
        if playlist:
            playlist_data = self.playlist_data(spot_id)
            if not playlist_data:
                return None
            track_no = playlist_data["tracks"]["total"]
            if track_no == 0:
                return None
            tracks = self.playlist_tracks(spot_id, track_no, requester)
            return playlist_data["name"], tracks
        else:
            track_data = self.track_data(spot_id)
            if not track_data:
                return None
            return None, [SimplifiedSpotifyTrack(track_data, requester)]

    async def play_tracks(self, ctx, player, tracks):
        not_found = 0
        for track in tracks:
            if not track:
                not_found += 1
                continue
            await player.queue.put(track)

        if not player.is_playing:
            await player.do_next()

    async def play(self, ctx, player, valid_spotify_link):
        requester = ctx.author
        result = self.prepare_tracks_for_youtube(valid_spotify_link, requester)
        if not result:
            return await ctx.send('No songs were found with that query. Please try again.', delete_after=8)
        playlist_name, tracks = result
        await self.play_tracks(ctx, player, tracks)
        if not playlist_name:
            return await ctx.send(f'```ini\nAdded {tracks[0].title} to the Queue\n```', delete_after=15)
        await ctx.send(
            f"```ini\nAdded the playlist {playlist_name} with {len(tracks)} songs to the queue.\n```", delete_after=8
        )

    # def check_id(self, accept_types, link):
    #     link_type, link_id = self.get_id(link)
    #     if link_type and link_type in accept_types:
    #         return True
    #     return False


class QueueExtension(asyncio.Queue):
    def shuffle(self):
        random.shuffle(self._queue)

    def list(self):
        return list(self._queue)
