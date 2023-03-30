import asyncio
import discord

from NotificationService import NotificationService
from SongQueue import SongQueue
from Youtube import YTDLSource


class MusicPlayer:
    def __init__(self, client: discord.Client):
        self.client = client
        self.song_queue = SongQueue(client)
        self.wait_for_audio_task = None
        self.is_paused = False

    async def queue_song(self, song_prompt: str, channel_id: int) -> None:
        """
        Adds a song to the queue
        :param song_prompt: The name of the song to add
        :param channel_id: The ID of the channel where the song was requested
        """
        await self.song_queue.add_song(song_prompt, channel_id)
        if self.wait_for_audio_task is None:
            print("Creating new audio wait task")
            self.wait_for_audio_task = self.client.loop.create_task(self._wait_for_audio_finish())
        else:
            requestor_channel = self.client.get_channel(channel_id)
            await self.song_queue.send_notification(requestor_channel)

    def stop(self) -> None:
        """Stops playing the current song and clears the queue"""
        self.song_queue.clear()
        self.is_paused = False
        if self.wait_for_audio_task:
            self.wait_for_audio_task.cancel()
            self.wait_for_audio_task = None
        if self.client.voice_clients:
            assert len(self.client.voice_clients) == 1
            self.client.voice_clients[0].stop()

    def skip(self, voice_client: discord.VoiceClient) -> None:
        """
        Skips the current song
        :param voice_client: A discord.VoiceClient object
        """
        voice_client.stop()
        self.is_paused = False

    def toggle_pause(self, voice_client: discord.VoiceClient) -> None:
        """
        Pauses or resumes the current song
        :param voice_client: A discord.VoiceClient object
        """
        if voice_client.is_playing():
            voice_client.pause()
            self.is_paused = True
        else:
            voice_client.resume()
            self.is_paused = False

    async def _wait_for_audio_finish(self) -> None:
        """
        A coroutine that waits for the current song to finish playing before playing the next song
        """
        assert len(self.client.voice_clients) == 1
        voice_client: discord.VoiceClient = self.client.voice_clients[0]

        # Bot should stay in VC if any of the following conditions
        while voice_client.is_playing() or self.is_paused or not self.song_queue.is_empty():
            # Play the next song in the queue
            if not voice_client.is_playing() and not self.is_paused and self.song_queue.is_next_song_ready():
                song = self.song_queue.pop()
                await self._play(voice_client, song.url, song.channel_id)

            await asyncio.sleep(1)
        await voice_client.disconnect()
        self.wait_for_audio_task = None

    async def _play(self, voice_client: discord.VoiceClient, song_prompt: str, channel_id: int) -> None:
        """
        Plays a song
        :param voice_client: A discord.VoiceClient object
        :param song_prompt: The URL of the song to play
        :param channel_id: The ID of the channel where the song was requested
        """
        song, filename = await YTDLSource.from_url(song_prompt)
        voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        await NotificationService.notify_new_song(self.client.get_channel(channel_id), song)
