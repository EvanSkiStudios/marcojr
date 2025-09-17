from typing import Optional
from discord import app_commands
from discord.ext import commands

from tools.weather_search.weather_api import slash_get_weather
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)


class Weather(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="weather", description="gets the weather")
    async def weather(self, interaction, city: Optional[str] = "", state: Optional[str] = ""):
        logger.debug(f'Command issued: weather by {interaction.user}, {city}, {state}')
        await interaction.response.defer()

        result = slash_get_weather(city, state)
        if not result:
            logger.error('Weather Error')
            await interaction.followup.send(f'Error getting weather for {city}, {state}')
            return

        await interaction.followup.send(result)


async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
