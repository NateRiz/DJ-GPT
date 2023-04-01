import discord
from discord import Interaction, Button


class MediaPlayback(discord.ui.View):
    @discord.ui.button(label="⏮", style=discord.ButtonStyle.blurple)
    async def rewind(self, interaction: Interaction, button: Button):
        ctx = await interaction.client.get_context(interaction.message)
        await interaction.client.get_command("rewind").callback(ctx)
        await interaction.response.defer()

    @discord.ui.button(label="⏸", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: Interaction, button: Button):
        ctx = await interaction.client.get_context(interaction.message)
        await interaction.client.get_command("pause").callback(ctx)
        await interaction.response.defer()

    @discord.ui.button(label="⏵", style=discord.ButtonStyle.green)
    async def play(self, interaction: Interaction, button: Button):
        ctx = await interaction.client.get_context(interaction.message)
        await interaction.client.get_command("play").callback(ctx)
        await interaction.response.defer()

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.danger)
    async def stop_(self, interaction: Interaction, button: Button):
        ctx = await interaction.client.get_context(interaction.message)
        await interaction.client.get_command("stop").callback(ctx)
        await interaction.response.defer()

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: Interaction, button: Button):
        ctx = await interaction.client.get_context(interaction.message)
        await interaction.client.get_command("skip").callback(ctx)
        await interaction.response.defer()
