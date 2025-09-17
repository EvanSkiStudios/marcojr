import os
from types import SimpleNamespace

from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from colt45 import colt_current_session_chat_cache
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)

# Load Env
load_dotenv()


def ns(d: dict) -> SimpleNamespace:
    """Convert dict into a dot-accessible namespace (recursively)."""
    return SimpleNamespace(**{k: ns(v) if isinstance(v, dict) else v for k, v in d.items()})


config_dict = {
    "MASTER_USER_ID": os.getenv("MASTER_USER_ID"),
}
CONFIG = ns(config_dict)


class Neuralize(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="neuralize", description="Empties the conversation cache")
    async def Neuralize(self, interaction):
        logger.debug(f'Command issued: neuralize by {interaction.user}')
        if interaction.user.id != int(CONFIG.MASTER_USER_ID):
            await interaction.response.send_message("The inner mechanisms of my mind are an enigma")
        else:
            colt_current_session_chat_cache.clear()
            await interaction.response.send_message(
                "https://tenor.com/view/men-in-black-mib-will-smith-u-saw-nothing-kharter-gif-12731469441707899432",
                delete_after=5
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Neuralize(bot))
