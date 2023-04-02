import asyncio
from asyncio import Task

import discord

from NotificationService import NotificationService
from Song import Song
from Youtube import YTDLSource


class SongQueue:
    def __init__(self, client: discord.Client):
        self.client = client
        # Lock to ensure multiple tasks dont simultaneously pop from the metadata queue
        self.metadata_task_queue_lock = asyncio.Lock()
        # Queue of tasks to grab metadata. Will be sent to song queue in order once done
        self.get_metadata_task_queue: list[tuple[Task, int, bool]] = []
        # Holds the metadata after retrieving the YouTube results
        self.song_queue = []

    async def add_song(self, search_prompt: str, channel_id: int, is_playlist: bool) -> None:
        """
        Add a song to the song metadata queue
        Args:
            search_prompt (str): Search prompt or YouTube link.
            channel_id (int): Discord channel ID.
            is_playlist (bool): Whether to queue up the entire playlist
        """
        print(f"added req {(search_prompt, channel_id, is_playlist)}")
        await self._get_metadata(search_prompt, channel_id, is_playlist)

    def is_empty(self) -> bool:
        """
        Check if the song queue is empty.
        Returns:
            bool: True if the song queue is empty, False otherwise.
        """
        return len(self.song_queue) == 0 and len(
            self.get_metadata_task_queue) == 0 and not self.metadata_task_queue_lock.locked()

    def pop(self) -> Song:
        """
        Pop the first song in the song queue.
        Returns:
            Song: The Song object that was popped from the queue.
        """
        return self.song_queue.pop(0)

    def is_next_song_ready(self) -> bool:
        """
        Check if there is a next song ready to be played.
        Returns:
            bool: True if there is a song in the song queue, False otherwise.
        """
        return len(self.song_queue) > 0

    def clear(self) -> None:
        """ Clear the song queue. """
        self.song_queue.clear()
        [task.cancel() for task, _ in self.get_metadata_task_queue]

    def length(self) -> int:
        """
        Get the length of the song queue.
        Returns:
            int: The number of songs in the song queue.
        """
        return len(self.song_queue)

    def get_song(self, index: int) -> Song:
        """
        Get a song from the song queue by its index.
        Args:
            index (int): The index of the song to get.
        Returns:
            Song: The Song object at the specified index.
        """
        return self.song_queue[index]

    async def send_notification(self, channel) -> None:
        """
        Send a queue notification to the channel
        :param channel: Channel
        """
        await NotificationService.notify_queued_song(channel, self.song_queue)

    async def _get_metadata(self, song_name: str, channel_id: int, is_playlist: bool) -> None:
        """
        Retrieve metadata for a song from YouTube and add it to the song metadata queue.
        Args:
            song_name (str): The name of the song or YouTube URL.
            channel_id (int): Discord channel ID.
        """
        print(f"Getting metadata for {song_name}")
        task = asyncio.create_task(YTDLSource.get_metadata(song_name, is_playlist))
        self.get_metadata_task_queue.append((task, channel_id))

        # Tasks must remain in order. Only add first done tasks.
        # Lock so that multiple async tasks aren't fight over the queue.
        async with self.metadata_task_queue_lock:
            while self.get_metadata_task_queue:
                try:
                    await self.get_metadata_task_queue[0][0]
                except Exception:
                    self.get_metadata_task_queue.pop(0)
                    raise
                finished_task, channel_id = self.get_metadata_task_queue.pop(0)
                songs_metadata: list[Song] = finished_task.result()
                print(f"Queueing song(s) {songs_metadata}")
                for sm in songs_metadata:
                    sm.channel_id = channel_id
                    self.song_queue.append(sm)
