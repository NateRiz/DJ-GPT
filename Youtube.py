import asyncio
import yt_dlp
import discord
from random import randint
from Song import Song

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'ytdl/audio.%(ext)s',  # You can change the PATH as you want
    'restrictfilenames': True,
    'noplaylist': True,
    'nocontinue': True,
    'nooverwrites': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1.0):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url) -> tuple[Song, str]:
        return await YTDLSource._retrieve(url)

    @classmethod
    async def _retrieve(cls, url, *, loop=None, stream=False) -> tuple[Song, str]:
        loop = loop or asyncio.get_event_loop()
        data = await execute_with_retries(loop, url, stream)
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        if stream:
            filename = data["title"]
        else:
            filename = ytdl.prepare_filename(data)
        song = Song(data["webpage_url"], data["title"], data["uploader"], data["duration"], data["thumbnail"], -1)
        return song, filename

    @classmethod
    async def get_metadata(cls, url) -> Song:
        try:
            task = await YTDLSource._retrieve(url, stream=True)
            return task[0]
        except Exception as e:
            print(e)


async def execute_with_retries(loop, url, stream):
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
    if data:
        return data

    retry_count = 3
    for _ in range(retry_count):
        await asyncio.sleep(randint(1, 5))  # Randomized to keep tasks on different seconds
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if data:
            return data
