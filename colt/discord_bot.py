import os
import re
import random

import discord

import discord_commands as bc
import discord_slash_commands as sc

from discord.ext import commands
from dotenv import load_dotenv
from types import SimpleNamespace

from discord_bot_users_manager import handle_bot_message
from tools.elevenlabs_voice import text_to_speech
from tools.search_determinator.job_determinator import is_search_request
from tools.web_search.internet_tool import llm_internet_search
from utility_scripts.system_logging import setup_logger
from colt45 import COLT_Create, COLT_Message, colt_current_session_chat_cache

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
    "THREADS": {
        "DISCUSSION": os.getenv("GMCD_NOT_ALLOWED_THREAD_D"),
        "NO_CONTEXT": os.getenv("GMCD_NOT_ALLOWED_THREAD_NC"),
        "DANEEL": os.getenv("GMCD_DANEEL_STINKY"),
    },
    "MASTER_USER_ID": os.getenv("MASTER_USER_ID"),
}
CONFIG = ns(config_dict)

channels_blacklist = [int(CONFIG.THREADS.DISCUSSION), int(CONFIG.THREADS.NO_CONTEXT), int(CONFIG.THREADS.DANEEL)]

# set discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.emojis_and_stickers = True

command_prefix = "🔫! "
client = commands.Bot(
    command_prefix=command_prefix,
    intents=intents,
    status=discord.Status.online
)
guild = discord.Object(id=CONFIG.BOT.SERVER_ID)


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        help_message = f"""
For Full documentation see: [The Github Repo](<https://github.com/EvanSkiStudios/marcojr>)
Commands are issued like so: `{command_prefix}<command> <argument>`
```Here are my commands:
"""
        for cog, commands_list in mapping.items():
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
    await client.tree.sync(guild=guild)
    # global
    try:
        synced = await client.tree.sync()
        logger.debug(f"Synced {len(synced)} global command(s)")
    except Exception as e:
        logger.error(e)


@client.event
async def on_disconnect():
    logger.error(f"{client.user} disconnected!")


@client.event
async def on_connect():
    logger.info(f"{client.user} connected!")


# ------- BOT COMMANDS ----------
@client.command(help="Changes Status to random or supplied custom")
async def status(ctx, *, arg=None):
    await bc.command_status(client, ctx, arg)


@client.command(help="Deletes the supplied Colt messages by id")
async def delete(ctx, *, arg=None):
    await bc.command_delete(client, ctx, arg)


@client.command(help="Sanity Check for input")
async def ping(ctx):
    await ctx.send("Pong!")


# ------- SLASH COMMANDS ----------
# noinspection PyUnresolvedReferences
@client.tree.command(name="draw", description="Ping test", guild=guild)
async def draw(interaction: discord.Interaction):
    logger.debug(f'Command issued: draw by {interaction.user}')
    await interaction.response.send_message("Pew Pew! 🔥🔫")


# noinspection PyUnresolvedReferences
@client.tree.command(name="search", description="search internet", guild=guild)
async def search(interaction: discord.Interaction, query: str):
    logger.debug(f'Command issued: search by {interaction.user}, {query}')
    await interaction.response.defer()  # shows "Bot is thinking..."

    response = await llm_internet_search(f"search the web for: {query}")
    await interaction.followup.send(f'Query: "{query}"\n' + response[0], suppress_embeds=True)


# noinspection PyUnresolvedReferences
@client.tree.command(name="tts", description="text to speech", guild=guild)
async def tts(interaction: discord.Interaction, text: str):
    logger.debug(f'Command issued: tts by {interaction.user}, {text}')
    await interaction.response.defer()

    tts_response = await text_to_speech(text, file_name=text)
    if tts_response is None:
        logger.error('TTS Error')

        number = random.randint(1, 100)
        # Check if the number is 45
        if number == 45:
            await interaction.followup.send('https://youtu.be/c4MAh9nCddc?t=5')
        else:
            await interaction.followup.send('Error making TTS. Probably out of cash.')
        return

    await interaction.followup.send(file=discord.File(tts_response))
    os.remove(tts_response)


# noinspection PyUnresolvedReferences
@client.tree.command(name="parrot", description="speak", guild=guild)
async def parrot(interaction: discord.Interaction, text: str):
    logger.debug(f'Command issued: parrot by {interaction.user}, {text}')

    if interaction.user.id != int(CONFIG.MASTER_USER_ID):
        await interaction.response.send_message("Squawk!")
    else:
        await interaction.response.send_message(f"{text}")


# noinspection PyUnresolvedReferences
@client.tree.command(name="neuralize", description="Empties the conversation cache", guild=guild)
async def neuralize(interaction: discord.Interaction):
    logger.debug(f'Command issued: neuralize by {interaction.user}')
    if interaction.user.id != int(CONFIG.MASTER_USER_ID):
        await interaction.response.send_message("The inner mechanisms of my mind are an enigma")
    else:
        colt_current_session_chat_cache.clear()
        await interaction.response.send_message(
            "https://tenor.com/view/men-in-black-mib-will-smith-u-saw-nothing-kharter-gif-12731469441707899432",
            delete_after=5
        )


# noinspection PyUnresolvedReferences
@client.tree.command(name="doom", description="plays doom", guild=guild)
async def doom(interaction: discord.Interaction):
    await interaction.response.defer()
    doom_gif = sc.play_doom()
    await interaction.followup.send(file=discord.File(doom_gif))


# ------- MESSAGE HANDLERS ---------
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
        message_is_request = is_search_request(message_content)
        if message_is_request:
            logger.info("Message is a Internet Search")
            response = await llm_internet_search(message_content)
        else:
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
        text = response[0]
        text_filtered = re.sub(r"\*(.*?)\*", r"[\1]", text)

        tts_file = await text_to_speech(text_filtered)
        if tts_file is None:
            logger.error('TTS Error')
            return

        if sent_message:
            await sent_message.reply(file=discord.File(tts_file))
        os.remove(tts_file)


@client.event
async def on_message(message):
    if message.channel.id in channels_blacklist:
        return
    
    await client.process_commands(message)

    message_content = message.clean_content
    username = message.author.name
    user_nickname = message.author.display_name

    channel = client.get_channel(message.channel.id)
    if not colt_current_session_chat_cache:
        async for past_message in channel.history(limit=20):
            author_name = past_message.author.name
            author_nick = past_message.author.display_name
            content = past_message.clean_content

            if past_message.author == client.user:
                message_prompt = {"role": "assistant", "content": f'{content}'}
            else:
                message_prompt = {"role": "user", "content": f'{author_name} ({author_nick}): \"{content}\"'}

            colt_current_session_chat_cache.append(message_prompt)
        # Reverse once so it's oldest → newest
        colt_current_session_chat_cache.reverse()
        logger.debug("Session Cache Created")
    else:
        # Only add new if cache already exists
        if message.author == client.user:
            message_prompt = {"role": "assistant", "content": f'{message_content}'}
        else:
            message_prompt = {"role": "user", "content": f'{username} ({user_nickname}): \"{message_content}\"'}
        colt_current_session_chat_cache.append(message_prompt)

    if message.mention_everyone:
        return
    if message_content.lower().find(command_prefix) != -1:
        return
    if message.author == client.user:
        return

    # DMs
    if isinstance(message.channel, discord.DMChannel):
        await llm_chat(message, username, user_nickname, message_content)
        return

    # replying to bot directly
    if message.reference:
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


# Startup discord Bot
client.run(CONFIG.BOT.TOKEN)
