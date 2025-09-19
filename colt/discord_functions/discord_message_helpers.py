import os
from collections import deque

import discord
from utility_scripts.system_logging import setup_logger
from dotenv import load_dotenv
from types import SimpleNamespace


# configure logging
logger = setup_logger(__name__)


def ns(d: dict) -> SimpleNamespace:
    """Convert dict into a dot-accessible namespace (recursively)."""
    return SimpleNamespace(**{k: ns(v) if isinstance(v, dict) else v for k, v in d.items()})


# Load Env
load_dotenv()

config_dict = {
    "THREADS_ALLOW": {
        "GMCD_CHANNEL_ID": os.getenv("GMCD_CHANNEL_ID"),
        "TEST_THREAD_ID": os.getenv("TEST_THREAD_ID")
    },
    "THREADS_DENY": {
        "DISCUSSION": os.getenv("GMCD_NOT_ALLOWED_THREAD_D"),
        "NO_CONTEXT": os.getenv("GMCD_NOT_ALLOWED_THREAD_NC"),
        "DANEEL": os.getenv("GMCD_DANEEL_STINKY")
    },
    "BOTS": {
        "SCUNGEONMASTER": os.getenv("BOT_ID_SCUNGE")
    }
}
CONFIG = ns(config_dict)
channels_blacklist = [int(v) for v in CONFIG.THREADS_DENY.__dict__.values()]
bots_blacklist = [int(b) for b in CONFIG.BOTS.__dict__.values()]
channels_whitelist = [int(t) for t in CONFIG.THREADS_ALLOW.__dict__.values()]


def should_ignore_message(client, message):
    if message.author in bots_blacklist:
        return True
    if message.channel.id not in channels_whitelist:
        return True
    if message.type == discord.MessageType.chat_input_command:
        return True
    if message.mention_everyone:
        return True
    if message.author == client.user:
        return True
    return False


# used for conversations
colt_current_session_chat_cache = deque(maxlen=40)


def session_chat_cache():
    global colt_current_session_chat_cache

    return colt_current_session_chat_cache


def clear_chat_cache():
    global colt_current_session_chat_cache
    colt_current_session_chat_cache.clear()


async def message_history_cache(client, message):
    global colt_current_session_chat_cache

    channel = client.get_channel(message.channel.id)
    if not colt_current_session_chat_cache:
        async for past_message in channel.history(limit=20):

            if past_message.type == discord.MessageType.chat_input_command:
                continue

            if past_message.author in bots_blacklist:
                continue

            if message.type == discord.MessageType.thread_created:
                continue

            author_name = past_message.author.name
            author_nick = past_message.author.display_name
            content = past_message.clean_content

            # if past_message.type == discord.MessageType.reply:

            if past_message.author == client.user:
                message_prompt = {"role": "assistant", "content": f'{content}'}
                assistant_prompt = None
            else:
                message_prompt = {"role": "user", "content": f'{author_name} ({author_nick}): \"{content}\"'}
                assistant_prompt = {"role": "assistant", "content": ''}

            colt_current_session_chat_cache.append(message_prompt)
            if assistant_prompt is not None:
                colt_current_session_chat_cache.append(assistant_prompt)
                assistant_prompt = None

        # Reverse once so it's oldest → newest
        colt_current_session_chat_cache.reverse()
        logger.debug("Session Cache Created")
        print(colt_current_session_chat_cache)
    else:
        message_content = message.clean_content
        author_name = message.author.name
        author_nick = message.author.display_name

        if message.type == discord.MessageType.reply:
            print(message.reference)
            print(f"Author: {message.author.name}")
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            print(f"Ref Auth:  {referenced_message.author.name}")

        # todo -- add replies

        # Only add new if cache already exists
        if message.author == client.user:
            message_prompt = {"role": "assistant", "content": f'{message_content}'}
            assistant_prompt = None
        else:
            message_prompt = {"role": "user", "content": f'{author_name} ({author_nick}): \"{message_content}\"'}
            assistant_prompt = {"role": "assistant", "content": ''}

        colt_current_session_chat_cache.append(message_prompt)
        if assistant_prompt is not None:
            colt_current_session_chat_cache.append(assistant_prompt)
            assistant_prompt = None

