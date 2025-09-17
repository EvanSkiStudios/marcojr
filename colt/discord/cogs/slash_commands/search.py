from discord import app_commands
from discord.ext import commands
from tools.web_search.internet_tool import llm_internet_search
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)


class Search(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="search", description="Search the internet")
    async def search(self, interaction, query: str):
        logger.debug(f'Command issued: search by {interaction.user}, {query}')
        await interaction.response.defer()
        response = await llm_internet_search(f"search the web for: {query}")
        await interaction.followup.send(response[0], suppress_embeds=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Search(bot))
