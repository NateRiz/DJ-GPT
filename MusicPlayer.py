import threading
import time

import discord

from SongQueue import SongQueue
from Youtube import YTDLSource


class MusicPlayer:
    def __init__(self, client):
        self.client = client
        self.song_queue = SongQueue()

    async def _play(self, voice_client, song_prompt, channel_id):
        song, filename = await YTDLSource.from_url(song_prompt)
        voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        threading.Thread(target=self.wait_for_audio_finish).start()
        requestor_channel = self.client.get_channel(channel_id)
        await requestor_channel.send(f'{song.url}\n**Now playing:** {song.name}: {song.duration}\n- {song.uploader}')

    def stop(self, voice_client):
        voice_client.stop()
        self.song_queue.clear()

    def toggle_pause(self, voice_client):
        if voice_client.is_playing():
            voice_client.pause()
        else:
            voice_client.resume()

    async def _queue_song(self, song_prompt, channel_id):
        song = await self.song_queue.add_song(song_prompt, channel_id)
        requestor_channel = self.client.get_channel(channel_id)
        await requestor_channel.send(F"**Added to queue**: {song.name}")

    async def play_or_queue_song(self, voice_client, song_prompt, channel_id):
        if voice_client.is_playing():
            await self._queue_song(song_prompt, channel_id)
        else:
            await self._play(voice_client, song_prompt, channel_id)

    def wait_for_audio_finish(self):
        assert len(self.client.voice_clients) == 1
        voice_client = self.client.voice_clients[0]

        while voice_client.is_playing():
            print("waiting ")
            time.sleep(1)

        self.client.loop.create_task(self._wait_for_audio_finish(voice_client))

    async def _wait_for_audio_finish(self, voice_client):
        if self.song_queue.is_empty():
            await voice_client.disconnect()
        else:
            song = self.song_queue.pop()
            await self._play(voice_client, song, song.channel_id)
