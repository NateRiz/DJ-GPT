import threading
import time

import discord

from NotificationService import NotificationService
from SongQueue import SongQueue
from Youtube import YTDLSource


class MusicPlayer:
    def __init__(self, client):
        self.client = client
        self.song_queue = SongQueue(client)
        self.audio_finish_lock = threading.Lock()
        self.has_song_started = False
        self.is_paused = False

    async def _play(self, voice_client, song_prompt, channel_id):
        song, filename = await YTDLSource.from_url(song_prompt)
        voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        self.has_song_started = True
        threading.Thread(target=self.wait_for_audio_finish).start()
        await NotificationService.notify_new_song(self.client.get_channel(channel_id), song, self.song_queue)

    def stop(self, voice_client):
        self.song_queue.clear()
        voice_client.stop()

    def skip(self, voice_client):
        voice_client.stop()

    def toggle_pause(self, voice_client):
        if voice_client.is_playing():
            voice_client.pause()
            self.is_paused = True
        else:
            voice_client.resume()
            self.is_paused = False

    def queue_song(self, song_prompt, channel_id):
        self.song_queue.add_song(song_prompt, channel_id)
        threading.Thread(target=self.wait_for_audio_finish).start()

    def wait_for_audio_finish(self):
        lock_acquired = self.audio_finish_lock.acquire(blocking=False)
        if not lock_acquired:
            print('player - Another thread is already running, skipping...')
            return

        assert len(self.client.voice_clients) == 1
        voice_client = self.client.voice_clients[0]

        while voice_client.is_playing() or self.is_paused or not self.song_queue.is_empty():
            if not voice_client.is_playing() and not self.is_paused and self.song_queue.is_next_song_ready():
                print("Queueing next song.")
                song = self.song_queue.pop()
                self.has_song_started = False
                self.client.loop.create_task(self._play(voice_client, song.url, song.channel_id))
                self._wait_for_song_to_start()

            time.sleep(2)

        self.client.loop.create_task(self._wait_for_audio_finish(voice_client))
        self.audio_finish_lock.release()
        print("Killed music player thread.")

    def _wait_for_song_to_start(self):
        while not self.has_song_started:
            time.sleep(1)

    async def _wait_for_audio_finish(self, voice_client):
        await voice_client.disconnect()
