import asyncio
import yt_dlp
import discord
from random import randint
from Song import Song


class YTDLSource(discord.PCMVolumeTransformer):
    song_ytdl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'outtmpl': 'ytdl/audio.%(ext)s',  # You can change the PATH as you want
        'noplaylist': True,
        'nocontinue': True,
        'nooverwrites': False,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    })
    playlist_ytdl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'outtmpl': 'ytdl/audio.%(ext)s',  # You can change the PATH as you want
        'noplaylist': False,
        'nocontinue': True,
        "ignoreerrors": True,
        'nooverwrites': False,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    })
    autoplay_ytdl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'outtmpl': 'ytdl/audio.%(ext)s',  # You can change the PATH as you want
        'nocontinue': True,
        'nooverwrites': False,
        'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
        'playlistrandom': True,
        "ignoreerrors": True,
        "max_downloads":1
    })

    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url) -> tuple[list[Song], str]:
        return await YTDLSource._retrieve(url, YTDLSource.song_ytdl)

    @classmethod
    async def _retrieve(cls, url, ytdl, *, loop=None, stream=False) -> tuple[list[Song], str]:
        loop = loop or asyncio.get_event_loop()
        data = await execute_with_retries(loop, url, stream, ytdl)
        filename = YTDLSource.song_ytdl.prepare_filename(data)

        entries = [data] if "entries" not in data else data["entries"]
        songs = []
        for entry in entries:
            if not entry:
                # Couldn't get one of the youtube links. Copyright or taken down, etc..
                continue
            song = Song(entry["webpage_url"], entry["title"], entry["uploader"], entry["duration"], entry["thumbnail"], -1)
            songs.append(song)

        return songs, filename

    @classmethod
    async def get_metadata(cls, url, is_playlist) -> list[Song]:
        try:
            ytdl = YTDLSource.playlist_ytdl if is_playlist else YTDLSource.song_ytdl
            task = await YTDLSource._retrieve(url, ytdl, stream=True)
            return task[0]
        except Exception as e:
            print(e)

    @classmethod
    async def get_autoplay(cls, query: str) -> tuple[list[Song], str]:
        try:
            return await YTDLSource._retrieve(f"ytsearchall:'{query}' playlist", YTDLSource.autoplay_ytdl)
        except Exception as e:
            print(e)


async def execute_with_retries(loop, url, stream, ytdl):
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
    except Exception as e:
        print(e)
    if data:
        return data

    retry_count = 3
    for _ in range(retry_count):
        await asyncio.sleep(randint(1, 5))  # Randomized to keep tasks on different seconds
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if data:
            return data
