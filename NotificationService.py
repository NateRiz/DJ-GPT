import asyncio

import discord

from Buttons.MediaPlayback import MediaPlayback
from Song import Song


class NotificationService:
    """Messages the channel for song and queue changes"""
    last_queue_message = None
    send_message_lock = asyncio.Lock()

    @staticmethod
    async def notify_new_song(channel: discord.TextChannel, song: Song) -> discord.Message:
        """
        Notify the channel of the newly added song and current song queue
        :param channel: The channel to send the notification to
        :param song: The newly added song
        :return: The message sent to the channel
        """
        embed = discord.Embed(
            title=song.name,
            url=song.url,
            description=format_duration(song.duration),
            color=0xFF0000,
        )
        embed.set_author(name=song.uploader)
        embed.set_thumbnail(url=song.thumbnail)
        await channel.send(embed=embed)
        NotificationService.last_queue_message = await channel.send(view=MediaPlayback())

    @staticmethod
    async def notify_queued_song(channel: discord.TextChannel, song_queue: list[Song]) -> None:
        """
        Notify the channel of the newly queued song and delete the last queue message
        :param channel: The channel to send the notification to
        :param song_queue: The current song queue
        """
        async with NotificationService.send_message_lock:
            if NotificationService.last_queue_message is not None:
                await NotificationService.last_queue_message.delete()

            description = []
            max_fields = 8
            num_fields = min(max_fields, len(song_queue))
            for i in range(num_fields):
                description.append(
                    f"{i + 1}. {song_queue[i].name} [{format_duration(song_queue[i].duration)}]")
            if len(song_queue) > max_fields:
                description.append(f"+ {len(song_queue) - max_fields} more...")

            song = song_queue[0]
            embed = discord.Embed(
                title=song.name,
                url=song.url,
                description="\n".join(description),
                color=0x00FFFF,
            )
            embed.set_author(name="Queue")
            embed.set_thumbnail(url=song.thumbnail)
            NotificationService.last_queue_message = await channel.send(embed=embed, view=MediaPlayback())


def format_duration(seconds: int) -> str:
    """
    Returns a formatted duration given the input time in seconds
    :param seconds: The input time in seconds
    :return: The formatted duration string
    """
    hours, minutes = divmod(seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
