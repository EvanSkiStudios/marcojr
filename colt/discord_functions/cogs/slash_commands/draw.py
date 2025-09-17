from discord import app_commands
from discord.ext import commands
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)


class Draw(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="draw", description="Ping test")
    async def Draw(self, interaction):
        logger.debug(f'Command issued: draw by {interaction.user}')
        await interaction.response.send_message("Pew Pew! 🔥🔫")


async def setup(bot: commands.Bot):
    await bot.add_cog(Draw(bot))
