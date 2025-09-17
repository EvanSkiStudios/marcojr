import os
import discord
from utility_scripts.system_logging import setup_logger
from dotenv import load_dotenv
from types import SimpleNamespace
from colt45 import colt_current_session_chat_cache

# configure logging
logger = setup_logger(__name__)


def ns(d: dict) -> SimpleNamespace:
    """Convert dict into a dot-accessible namespace (recursively)."""
    return SimpleNamespace(**{k: ns(v) if isinstance(v, dict) else v for k, v in d.items()})


# Load Env
load_dotenv()

config_dict = {
    "THREADS": {
        "DISCUSSION": os.getenv("GMCD_NOT_ALLOWED_THREAD_D"),
        "NO_CONTEXT": os.getenv("GMCD_NOT_ALLOWED_THREAD_NC"),
        "DANEEL": os.getenv("GMCD_DANEEL_STINKY"),
    },
    "BOTS": {
        "SCUNGEONMASTER": os.getenv("BOT_ID_SCUNGE")
    }
}
CONFIG = ns(config_dict)
channels_blacklist = [int(v) for v in CONFIG.THREADS.__dict__.values()]
bots_blacklist = [int(b) for b in CONFIG.BOTS.__dict__.values()]


def should_ignore_message(client, message):
    if message.author in bots_blacklist:
        return True
    if message.channel.id in channels_blacklist:
        return True
    if message.type == discord.MessageType.chat_input_command:
        return True
    if message.mention_everyone:
        return True
    if message.author == client.user:
        return True
    return False


async def message_history_cache(client, message, message_content, username, user_nickname):
    channel = client.get_channel(message.channel.id)
    if not colt_current_session_chat_cache:
        async for past_message in channel.history(limit=20):

            if past_message.type == discord.MessageType.chat_input_command:
                continue

            if past_message.author in bots_blacklist:
                continue

            # if past_message.type == discord_functions.MessageType.reply:

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
        # if past_message.type == discord_functions.MessageType.reply:

        # Only add new if cache already exists
        if message.author == client.user:
            message_prompt = {"role": "assistant", "content": f'{message_content}'}
        else:
            message_prompt = {"role": "user", "content": f'{username} ({user_nickname}): \"{message_content}\"'}
        colt_current_session_chat_cache.append(message_prompt)
