import asyncio
import re
from builtins import ExceptionGroup

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
    """
    # Ignore the bot
    if message.author == client.user:
        return

    if message.content.startswith(command_prefix):
        words = message.content.split()
        # Lowercase the first command
        words[0] = words[0].lower()
        # Join the words back into a string
        lowercase_message = " ".join(words)
        message.content = lowercase_message

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


@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return

    if reaction.emoji != '🎵':
        return

    message = reaction.message.content.split()
    max_url_length = 164
    url = message[-2][:max_url_length]
    if not is_playlist_url(url):
        return

    ctx = await client.get_context(reaction.message.reference.resolved)
    await playlist(ctx, url)
    await reaction.message.delete()

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

    try:
        await ctx.message.add_reaction('🕘')
        await music_player.queue_song(song_prompt, ctx.channel.id)
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('✅')
    except Exception as e:
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('❌')
        await ctx.send(str(e))

    if is_playlist_url(song_prompt):
        response = await ctx.message.reply(
            F"This url looks like a playlist. To queue up all songs in a playlist use the `-playlist` command or click the reaction below:\n\n` -playlist {song_prompt} `")
        await response.add_reaction('🎵')


@client.command()
async def playlist(ctx: Context, *args: str) -> None:
    """
    A command that plays a playlist in a voice channel
    :param ctx: The context object for the command
    :param args: The arguments passed to the command
    :return: None
    """
    if ctx.voice_client is None:
        is_connected = await connect(ctx)
        if not is_connected:
            return

    playlist_url = "".join(args)
    if not is_playlist_url(playlist_url):
        await ctx.send(F"Not a valid youtube playlist url: {playlist_url}")
        return

    try:
        await ctx.message.add_reaction('🕘')
        await music_player.queue_playlist(playlist_url, ctx.channel.id)
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('✅')
    except Exception as e:
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction('❌')
        await ctx.send(str(e))


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
        await ctx.send("No voice state in context")
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


@client.command(aliases=["back"])
async def rewind(ctx: Context) -> None:
    voice_client = ctx.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return
    music_player.rewind(voice_client)


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


def is_playlist_url(url):
    playlist_regex = r".*youtube\.com\/watch\?v=.*&list=.*"
    return re.match(playlist_regex, url) is not None


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
# button to requeue past songs.
