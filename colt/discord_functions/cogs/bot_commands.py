from discord.ext import commands

from discord_functions import discord_commands as bc
from utility_scripts.system_logging import setup_logger

# configure logging
logger = setup_logger(__name__)


class Utility(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(help="Sanity Check for input")
    async def ping(self, ctx):
        await ctx.send("Pong!")

    @commands.command(help="Changes Status to random or supplied custom")
    async def status(self, ctx, *, arg=None):
        await bc.command_status(self.client, ctx, arg)

    @commands.command(help="Deletes the supplied Colt messages by id")
    async def delete(self, ctx, *, arg=None):
        await bc.command_delete(self.client, ctx, arg)

    @commands.command(help="test")
    async def test(self, ctx):
        await ctx.send("Pew Pew! 🔥🔫")


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
