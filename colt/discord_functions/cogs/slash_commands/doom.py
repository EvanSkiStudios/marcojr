import os
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)


class Doom(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="doom", description="plays doom")
    async def Doom(self, interaction):
        logger.debug(f'Command issued: Doom by {interaction.user}')
        await interaction.response.defer()
        doom_file = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "doom.gif"
        doom_path = os.path.abspath(doom_file)
        await interaction.followup.send(file=discord.File(doom_path))


async def setup(bot: commands.Bot):
    await bot.add_cog(Doom(bot))
