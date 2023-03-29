import asyncio

import discord
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context

from MusicPlayer import MusicPlayer
from SECRETS import TOKEN

command_prefix = "-"
client = commands.Bot(command_prefix=command_prefix, intents=discord.Intents().all())
music_player = MusicPlayer(client)


@client.event
async def on_message(message: Message) -> None:
    """
    An event that is triggered when a message is received in the server
    :param message: The message object that was received
    :return: None
    """
    if message.author == client.user:
        return

    if message.content.startswith(command_prefix):
        await client.process_commands(message)


@client.event
async def on_voice_state_update(member, _before, after):
    """
    Used when bot disconnects from the channel to clear the music player
    :param member: member
    :param _before: Channel before
    :param after: Channel after
    """
    if after.channel is None and member == client.user:
        music_player.stop()


@client.after_invoke
async def delete_command_message(ctx: Context) -> None:
    """
    An event that is triggered after a command is invoked. This function waits for 60 seconds,
    then deletes the message that triggered the command
    :param ctx: The context object for the command
    :return: None
    """
    await asyncio.sleep(60)
    await ctx.message.delete()


@client.event
async def on_ready() -> None:
    """
    An event that is triggered when the client has successfully connected to Discord
    :return: None
    """
    print("successful login as {0.user}".format(client))


@client.command()
async def play(ctx: Context, *args: str) -> None:
    """
    A command that plays music in a voice channel
    :param ctx: The context object for the command
    :param args: The arguments passed to the command
    :return: None
    """
    song_prompt = " ".join(args) if args else None
    if ctx.voice_client is None:
        if not song_prompt:
            await ctx.send(F"Nothing to play.")
            return

        is_connected = await connect(ctx)
        if not is_connected:
            return

    else:  # Connected to VC
        if not song_prompt:
            music_player.toggle_pause(ctx.voice_client)
            return

    await music_player.queue_song(song_prompt, ctx.channel.id)


@client.command()
async def connect(ctx: Context) -> bool:
    """
    A command that connects the bot to a voice channel
    :param ctx: The context object for the command
    :return: A boolean indicating if the bot successfully connected to the voice channel
    """
    if ctx.voice_client is not None:
        return False

    voice_state = ctx.message.author.voice
    if voice_state is not None:
        await voice_state.channel.connect()
        return True
    else:
        await ctx.send("Not connected to any voice channel")
        return False


@client.command()
async def pause(ctx: Context) -> None:
    """
    A command that pauses the currently playing song
    :param ctx: The context object for the command
    :return: None
    """
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return

    music_player.toggle_pause(voice_client)


@client.command(aliases=["forceskip"])
async def skip(ctx: Context) -> None:
    """
    A command that skips the currently playing song
    :param ctx: The context object for the command
    :return: None
    """
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return

    if voice_client.is_playing() or music_player.is_paused:
        music_player.skip(voice_client)
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@client.command(aliases=["dc", "stop"])
async def disconnect(ctx: Context) -> None:
    """
    A command that disconnects the bot from the voice channel
    :param ctx: The context object for the command
    :return: None
    """
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return
    else:
        await voice_client.disconnect()


if __name__ == '__main__':
    # getting the secret token
    client.run(TOKEN)

# todo
# voice to text
# Queue promote to first or delete
# playlist
# download future songs so they play faster. Have a cleanup task that deletes old songs
# loading bar for download song
# Disconnecting the bot in right click menu breaks it (for a little while?)
