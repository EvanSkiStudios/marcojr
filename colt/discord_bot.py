import os
import re

import discord

import discord_commands as bc

from discord.ext import commands
from dotenv import load_dotenv

import random

from discord_bot_users_manager import handle_bot_message
from test_scripts.elevenlabs_voice import text_to_speech
from tools.search_determinator.job_determinator import is_search_request
from tools.web_search.internet_tool import llm_internet_search
from utility_scripts.system_logging import setup_logger
from colt45 import COLT_Create, COLT_Message, colt_current_session_chat_cache

# configure logging
logger = setup_logger(__name__)

# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")

BOT_SERVER_ID = os.getenv("GMCD_SERVER_ID")
BOT_TEST_SERVER_ID = os.getenv("TEST_SERVER_ID")
BOT_DM_CHANNEL_ID = os.getenv("DM_CHANNEL_ID")
BOT_CHANNEL_ID = os.getenv("GMCD_CHANNEL_ID")

GMC_DISCUSSION_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD_D")
GMC_NO_CONTEXT_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD_NC")
GMC_DANEEL_THREAD = os.getenv("GMCD_DANEEL_STINKY")

channels_blacklist = [GMC_DISCUSSION_THREAD, GMC_NO_CONTEXT_THREAD, GMC_DANEEL_THREAD]

# set discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.emojis = True
intents.emojis_and_stickers = True

command_prefix = "M! "
client = commands.Bot(
    command_prefix=command_prefix,
    intents=intents,
    status=discord.Status.online
)
guild = discord.Object(id=BOT_SERVER_ID)


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        help_message = """
For Full documentation see: [The Github Repo](<https://github.com/EvanSkiStudios/marcojr>)
Commands are issued like so: `M! <command> <argument>`
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
    print(f'We have logged in as {client.user}')
    await client.tree.sync(guild=guild)
    # global
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} global command(s)")
    except Exception as e:
        print(e)


@client.event
async def on_disconnect():
    print(f"{client.user} disconnected!")


@client.event
async def on_connect():
    print(f"{client.user} connected!")


@client.event
async def on_close():
    print(f"{client.user} closed!")


# ------- BOT COMMANDS ----------
@client.command(help="Changes Status to random or supplied custom")
async def status(ctx, *, arg=None):
    await bc.command_status(client, ctx, arg)


@client.command(help="Deletes the supplied Colt messages by id")
async def delete(ctx, *, arg=None):
    await bc.command_delete(client, ctx, arg)


@client.command(help="Sanity Check for input")
async def ping(ctx):
    await ctx.send(f"Pong!")


# ------- SLASH COMMANDS ----------
# noinspection PyUnresolvedReferences
@client.tree.command(name="draw", description="Ping test", guild=guild)
async def draw(interaction: discord.Interaction):
    await interaction.response.send_message("Pew Pew! 🔥🔫")


# noinspection PyUnresolvedReferences
@client.tree.command(name="search", description="search internet", guild=guild)
async def search(interaction: discord.Interaction, query: str):
    # tell Discord we are working on it
    await interaction.response.defer()  # shows "Bot is thinking..."

    response = await llm_internet_search(f"search the web for: {query}")
    await interaction.followup.send(f'Query: "{query}"\n' + response[0], suppress_embeds=True)


# noinspection PyUnresolvedReferences
@client.tree.command(name="tts", description="text to speech", guild=guild)
async def search(interaction: discord.Interaction, text: str):
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
            logger.info(f"Message is a Internet Search")
            response = await llm_internet_search(message_content)
        else:
            response = await COLT_Message(username, user_nickname, message_content)

    if response == -1:
        return

    # response should have been split in the above function returns
    for i, part in enumerate(response):
        if not message.author.bot and i == 0:
            sent_message = await message.reply(part, suppress_embeds=True)
        else:
            await message.channel.send(part, suppress_embeds=True)

    if is_tts_message:
        text = response[0]
        if text is None:
            logger.error('TTS Error')
            return
        text_filtered = re.sub(r"\*(.*?)\*", r"[\1]", text)

        tts_file = await text_to_speech(text_filtered)
        if sent_message:
            await sent_message.reply(file=discord.File(tts_file))
        os.remove(tts_file)


@client.event
async def on_message(message):
    if str(message.channel.id) in channels_blacklist:
        return
    
    await client.process_commands(message)

    message_content = message.content
    username = message.author.name
    user_nickname = message.author.display_name

    for user in message.mentions:
        message_content = message_content.replace(f"<@{user.id}>", f"@{user.name}")
        message_content = message_content.replace(f"<@!{user.id}>", f"@{user.name}")

    channel = client.get_channel(message.channel.id)
    if not colt_current_session_chat_cache:
        async for past_message in channel.history(limit=20):
            user = past_message.author.name
            user_nick = past_message.author.display_name
            content = past_message.content
            for user in past_message.mentions:
                content = content.replace(f"<@{user.id}>", f"@{user.name}")
                content = content.replace(f"<@!{user.id}>", f"@{user.name}")

            if past_message.author == client.user:
                message_prompt = {"role": "assistant", "content": f'{content}'}
            else:
                message_prompt = {"role": "user", "content": f'{user} ({user_nick}): \"{content}\"'}

            colt_current_session_chat_cache.append(message_prompt)
        # Reverse once so it's oldest → newest
        colt_current_session_chat_cache.reverse()
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
        # print(f"{message_content}")
        await llm_chat(message, username, user_nickname, message_content)
        return

    # replying to bot directly
    if message.reference:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            message_content = message_content.replace(f"<@{BOT_APPLICATION_ID}>", "")
            await llm_chat(message, username, user_nickname, message_content)
            return

    # ping
    if client.user.mentioned_in(message):
        message_content = message_content.replace(f"<@{BOT_APPLICATION_ID}>", "Colt ")
        await llm_chat(message, username, user_nickname, message_content)
        return

    # if the message includes "colt " it will trigger and run the code
    if re.search(r"\bcolt[\s,.?!]", message_content.lower()):
        await llm_chat(message, username, user_nickname, message_content)
        return

    if message_content.lower().endswith('colt'):
        await llm_chat(message, username, user_nickname, message_content)
        return


# Startup discord Bot
client.run(BOT_TOKEN)
