import os
import random

import discord
from discord import app_commands
from discord.ext import commands

from tools.elevenlabs_voice import text_to_speech
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)


class TTS(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="tts", description="text to speech")
    async def tts(self, interaction, text: str):
        logger.debug(f'Command issued: tts by {interaction.user}, {text}')
        await interaction.response.defer()

        tts_file = await text_to_speech(text, file_name=text)
        if not tts_file:
            logger.error('TTS Error')

            # 🎲 Easter Egg: 1 in 100 chance to drop Colt-45 gag
            if random.randint(1, 100) == 45:
                await interaction.followup.send('https://youtu.be/c4MAh9nCddc?t=5')
            else:
                await interaction.followup.send('Error making TTS. Probably out of cash.')
            return

        await interaction.followup.send(file=discord.File(tts_file))
        os.remove(tts_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(TTS(bot))
