import threading
import time

import discord
from discord.ext import commands

from MusicPlayer import MusicPlayer
from SECRETS import TOKEN

intents = discord.Intents().all()
client = commands.Bot(command_prefix='-', intents=intents)
music_player = MusicPlayer(client)


@client.after_invoke
async def delete_command_message(ctx):
    # Delete the user's command message
    await ctx.message.delete()

@client.event
async def on_ready():
    print("successful login as {0.user}".format(client))


@client.command()
async def play(ctx, *args):
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

    music_player.queue_song(song_prompt, ctx.channel.id)


@client.command()
async def connect(ctx):
    voice_state = ctx.message.author.voice
    if voice_state is not None:
        await voice_state.channel.connect()
        return True
    else:
        await ctx.send("Not connected to any voice channel")
        return False


@client.command()
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return

    music_player.toggle_pause(voice_client)


@client.command()
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return

    if voice_client.is_playing():
        music_player.stop(voice_client)
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    await voice_client.disconnect()

@client.command()
async def forceskip(ctx):
    await skip(ctx)

@client.command()
async def skip(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send("Not connected to any voice channel")
        return

    if voice_client.is_playing():
        music_player.skip(voice_client)
    else:
        await ctx.send("The bot is not playing anything at the moment.")


@client.command()
async def dc(ctx):
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
# check if arg is youtube link or search prompts
# queue skip
# Queue promote to first
# playlist
