import discord

from Song import Song


class NotificationService:
    """Messages the channel for song and queue changes"""
    last_queue_message = None

    @staticmethod
    async def notify_new_song(channel: discord.TextChannel, song: Song, song_queue) -> discord.Message:
        """
        Notify the channel of the newly added song and current song queue
        :param channel: The channel to send the notification to
        :param song: The newly added song
        :param song_queue: The current song queue
        :return: The message sent to the channel
        """
        description = []
        max_fields = 8
        num_fields = min(max_fields, song_queue.length())
        for i in range(num_fields):
            description.append(f"{i + 1}. {song_queue.get_song(i).name} {song_queue.get_song(i).duration}")
        if song_queue.length() > max_fields:
            description.append(f"+ {song_queue.length() - max_fields} more...")

        embed = discord.Embed(
            title=song.name,
            url=song.url,
            description="\n".join(description),
            color=0x00FFFF,
        )
        embed.set_author(name="Song Queue")
        embed.set_thumbnail(url=song.thumbnail)
        return await channel.send(embed=embed)

    @staticmethod
    async def notify_queued_song(channel: discord.TextChannel, song: Song, song_queue) -> discord.Message:
        """
        Notify the channel of the newly queued song and delete the last queue message
        :param channel: The channel to send the notification to
        :param song: The newly queued song
        :param song_queue: The current song queue
        :return: The message sent to the channel
        """
        if NotificationService.last_queue_message is not None:
            await NotificationService.last_queue_message.delete()

        NotificationService.last_queue_message = await NotificationService.notify_new_song(channel, song, song_queue)
        return NotificationService.last_queue_message
