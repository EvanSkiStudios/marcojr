import asyncio
import os
import re

import discord

import discord_commands as bc

from discord.ext import commands
from dotenv import load_dotenv

from colt45 import COLT_Create, COLT_Message, colt_current_session_chat_cache

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

emote_dict = {}


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
async def ping(ctx, *, arg=None):
    await ctx.send(f"Pong!")


# ------- MESSAGE HANDLERS ---------
async def llm_chat(message, username, user_nickname, message_content):
    async with message.channel.typing():
        response = await COLT_Message(username, user_nickname, message_content)

    if response == -1:
        return

    for i, part in enumerate(response):
        if not message.author.bot and i == 0:
            await message.reply(part)
            # message_id = sent_message.id
        else:
            await message.channel.send(part)


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

            colt_current_session_chat_cache.append(f'{user} ({user_nick}): \"{content}\"')
        # Reverse once so it's oldest → newest
        colt_current_session_chat_cache.reverse()
    else:
        # Only add new if cache already exists
        colt_current_session_chat_cache.append(f'{username} ({user_nickname}): \"{message_content}\"')

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
