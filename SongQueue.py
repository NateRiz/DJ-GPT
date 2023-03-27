import asyncio
import threading

from NotificationService import NotificationService
from Youtube import YTDLSource


class SongQueue:
    def __init__(self, client):
        self.client = client
        # Holds only the search prompts
        self.request_queue = []
        self.metadata_download_lock = threading.Lock()

        # Holds the metadata after retrieving the youtube results
        self.song_queue = []

    def add_song(self, song_name, channel_id):
        self.request_queue.append((song_name, channel_id))
        print(f"added req - now {self.request_queue}")
        threading.Thread(target=self._get_metadata).start()

    def _get_metadata(self):
        lock_acquired = self.metadata_download_lock.acquire(blocking=False)
        if not lock_acquired:
            print('metadata - Another thread is already running, skipping...')
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        future = asyncio.Future()

        while self.request_queue:
            song_name, channel_id = self.request_queue.pop(0)
            try:
                result = loop.run_until_complete(YTDLSource.get_metadata(song_name))
                future.set_result(result)
                song, _ = result
                song.channel_id = channel_id
                if self.song_queue:
                    self.client.loop.create_task(self.send_notification(song))
                self.song_queue.append(song)
            except Exception as e:
                print(f"Failed to queue up song: {song_name}.Got Exception:\n{e}")


        self.metadata_download_lock.release()
        loop.close()
        print("Killed song queue thread.")


    def is_empty(self):
        """ Not empty if any of the following conditions are true:
        1. Song queue is not empty
        2. Request/Command queue is not empty
        3. thread locked - in the process of downloading song metadata.
        """
        return len(self.song_queue) == 0 and len(self.request_queue) == 0 and not self.metadata_download_lock.locked()

    def pop(self):
        return self.song_queue.pop(0)

    def top(self):
        return self.song_queue[0]

    def is_next_song_ready(self):
        return len(self.song_queue) > 0

    def clear(self):
        self.song_queue.clear()
        self.request_queue.clear()

    def length(self):
        return len(self.song_queue)

    def get_song(self, index):
        return self.song_queue[index]

    async def send_notification(self, song):
        requestor_channel = self.client.get_channel(song.channel_id)
        await NotificationService.notify_queued_song(requestor_channel, song, self)
