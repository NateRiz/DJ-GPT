from Song import Song
from Youtube import YTDLSource
from dataclasses import dataclass


class SongQueue:
    def __init__(self):
        self.queue = []

    async def add_song(self, song_name, channel_id):
        song, _ = await YTDLSource.get_metadata(song_name)
        self.queue.append(song)
        return song

    def is_empty(self):
        return len(self.queue) == 0

    def pop(self):
        return self.queue.pop(0)

    def clear(self):
        self.queue.clear()
