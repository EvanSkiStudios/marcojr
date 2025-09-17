import os
import re

import discord

from discord.ext import commands
from dotenv import load_dotenv
from types import SimpleNamespace

from discord_functions.discord_bot_users_manager import handle_bot_message
from discord_functions.discord_message_helpers import should_ignore_message, message_history_cache
from tools.determine_request import classify_request
from tools.elevenlabs_voice import text_to_speech
from tools.weather_search.weather_tool import weather_search
from tools.web_search.internet_tool import llm_internet_search
from utility_scripts.system_logging import setup_logger
from colt45 import COLT_Create, COLT_Message

# configure logging
logger = setup_logger(__name__)

# Load Env
load_dotenv()


def ns(d: dict) -> SimpleNamespace:
    """Convert dict into a dot-accessible namespace (recursively)."""
    return SimpleNamespace(**{k: ns(v) if isinstance(v, dict) else v for k, v in d.items()})


config_dict = {
    "BOT": {
        "TOKEN": os.getenv("TOKEN"),
        "APPLICATION_ID": os.getenv("APPLICATION_ID"),
        "SERVER_ID": os.getenv("GMCD_SERVER_ID"),
        "TEST_SERVER_ID": os.getenv("TEST_SERVER_ID"),
        "DM_CHANNEL_ID": os.getenv("DM_CHANNEL_ID"),
        "CHANNEL_ID": os.getenv("GMCD_CHANNEL_ID"),
    },
    "MASTER_USER_ID": os.getenv("MASTER_USER_ID"),
}
CONFIG = ns(config_dict)

# set discord_functions intents
intents = discord.Intents.default()
intents.message_content = True
intents.emojis_and_stickers = True


class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs here
        cogs = [
            "discord_functions.cogs.bot_commands",
            "discord_functions.cogs.slash_commands.doom",
            "discord_functions.cogs.slash_commands.neuralize",
            "discord_functions.cogs.slash_commands.parrot",
            "discord_functions.cogs.slash_commands.search",
            "discord_functions.cogs.slash_commands.tts",
            "discord_functions.cogs.slash_commands.weather"
        ]
        for cog in cogs:
            await self.load_extension(cog)

        # 👇 Sync all commands to one guild
        guild = discord.Object(id=CONFIG.BOT.SERVER_ID)
        self.tree.copy_global_to(guild=guild)  # copy any global commands
        await self.tree.sync(guild=guild)  # sync them instantly


command_prefixes = ["🔫! ", ":gun:! ", "M! "]
client = MyBot(
    command_prefix=command_prefixes,
    intents=intents,
    status=discord.Status.online
)


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        help_message = f"""
For Full documentation see: [The Github Repo](<https://github.com/EvanSkiStudios/marcojr>)
Commands are issued like so: `{command_prefixes}<command> <argument>`
```Here are my commands:
"""
        for command_cog, commands_list in mapping.items():
            for command in commands_list:
                help_message += f"`{command.name}` - {command.help or 'No description'}\n"
        help_message += "```"
        await self.get_destination().send(help_message)


# assign help command from bot_commands
client.help_command = MyHelpCommand()

# Startup LLM
COLT_Create()


# --------- BOT EVENTS ---------
@client.event
async def on_ready():
    # When the bot has logged in, call back
    logger.info(f'We have logged in as {client.user}')
    # await client.tree.sync(guild=discord_functions.Object(id=CONFIG.BOT.SERVER_ID))


@client.event
async def on_disconnect():
    logger.error(f"{client.user} disconnected!")


@client.event
async def on_connect():
    logger.info(f"{client.user} connected!")


# ------- MESSAGE HANDLERS ---------
async def send_tts(interaction_or_message, text, reply_target=None):
    text_filtered = re.sub(r"\*(.*?)\*", r"[\1]", text)
    tts_file = await text_to_speech(text_filtered)
    if not tts_file:
        logger.error('TTS Error')
        await (interaction_or_message.followup.send if hasattr(interaction_or_message, "followup")
               else interaction_or_message.channel.send)("Error making TTS.")
        return
    if reply_target:
        await reply_target.reply(file=discord.File(tts_file))
    else:
        if hasattr(interaction_or_message, "followup"):
            await interaction_or_message.followup.send(file=discord.File(tts_file))
        else:
            await interaction_or_message.channel.send(file=discord.File(tts_file))
    os.remove(tts_file)


async def llm_chat(message, username, user_nickname, message_content):
    if message.author.bot:
        result = handle_bot_message(username)
        if result == -1:
            return

    is_tts_message = False
    if not message.author.bot and re.search(r"\(tts\)", message_content, re.IGNORECASE):
        logger.debug('Message is a TTS Message')
        is_tts_message = True
        message_content = re.sub(r"\(tts\)", "", message_content, flags=re.IGNORECASE)

    async with message.channel.typing():
        request_classification = classify_request(message_content)

        logger.info(f"Classification={request_classification}, Content={message_content}")

        match request_classification:
            case "weather_search":
                response = await weather_search(message_content)

            case "search":
                response = await llm_internet_search(message_content)

            case _:
                response = await COLT_Message(username, user_nickname, message_content)

    if response == -1:
        return

    # response should have been split in the above function returns
    sent_message = None
    for i, part in enumerate(response):
        if not message.author.bot and i == 0:
            sent_message = await message.reply(part, suppress_embeds=True)
        else:
            await message.channel.send(part, suppress_embeds=True)

    if is_tts_message:
        await send_tts(message, response[0], reply_target=sent_message)


@client.event
async def on_message(message):
    if should_ignore_message(client, message):
        return

    await client.process_commands(message)

    if any(message.content.startswith(prefix) for prefix in command_prefixes):
        return True

    # gather message data
    message_content = message.clean_content
    username = message.author.name
    user_nickname = message.author.display_name

    await message_history_cache(client, message, message_content, username, user_nickname)

    if message.attachments:
        for media in message.attachments:
            content_type = str(media.content_type).lower()

    # DMs
    if isinstance(message.channel, discord.DMChannel):
        await llm_chat(message, username, user_nickname, message_content)
        return

    # replying to bot directly
    if message.reference:
        if message.type == discord.MessageType.thread_created:
            return
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            await llm_chat(message, username, user_nickname, message_content)
            return

    # ping
    if client.user.mentioned_in(message):
        await llm_chat(message, username, user_nickname, message_content)
        return

    # if the message includes "colt " it will trigger and run the code
    if re.search(r"\bcolt[\s,.?!]", message_content, re.IGNORECASE):
        await llm_chat(message, username, user_nickname, message_content)
        return

    if message_content.lower().endswith('colt'):
        await llm_chat(message, username, user_nickname, message_content)
        return


# Startup discord_functions Bot
client.run(CONFIG.BOT.TOKEN)
