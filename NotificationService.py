import discord


class NotificationService:
    last_queue_message = None

    @staticmethod
    async def notify_new_song(channel, song, song_queue):
        description = []
        max_fields = 8
        num_fields = min(max_fields, song_queue.length())
        for i in range(num_fields):
            description.append(F"{i + 1}. {song_queue.get_song(i).name} {song_queue.get_song(i).duration}")
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
    async def notify_queued_song(channel, song, song_queue):
        if NotificationService.last_queue_message is not None:
            await NotificationService.last_queue_message.delete()

        NotificationService.last_queue_message = await NotificationService.notify_new_song(channel, song, song_queue)
