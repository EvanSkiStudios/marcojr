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
    logger.debug(colt_current_session_chat_cache)


async def message_history_cache(client, message):
    global colt_current_session_chat_cache

    def build_user_prompt(author, nick, content, reply_to=None):
        """Helper to format user messages (with optional reply)."""
        if reply_to:
            return {
                "role": "user",
                "content": f'{author} ({nick}) (Replying to: {reply_to}): "{content}"'
            }
        return {"role": "user", "content": f'{author} ({nick}): "{content}"'}

    def build_assistant_prompt(content=""):
        """Helper to format assistant messages."""
        return {"role": "assistant", "content": content}

    async def process_message(msg):
        """Process a single Discord message into prompts."""
        # Skip irrelevant messages
        if msg.type in {discord.MessageType.chat_input_command, discord.MessageType.thread_created}:
            return []
        if msg.author in bots_blacklist:
            return []

        author_name = msg.author.name
        author_nick = msg.author.display_name
        content = msg.clean_content

        # Assistant (bot) message
        if msg.author.id == client.user.id:
            return [build_assistant_prompt(content)]

        # Reply message
        if msg.type == discord.MessageType.reply and msg.reference:
            referenced = await msg.channel.fetch_message(msg.reference.message_id)
            prompts = [
                build_user_prompt(author_name, author_nick, content, referenced.author.name)
            ]
            return prompts

        # Regular user message
        prompts = [build_user_prompt(author_name, author_nick, content)]
        return prompts

    # First-time cache build
    if not colt_current_session_chat_cache:
        channel = client.get_channel(message.channel.id)
        history_prompts = []
        async for past_message in channel.history(limit=20):
            history_prompts.extend(await process_message(past_message))

        colt_current_session_chat_cache.extend(reversed(history_prompts))
        logger.debug("Session Cache Created")
        return

    # Incremental update (no assistant prompt for user messages here)
    new_prompts = await process_message(message)
    colt_current_session_chat_cache.extend(new_prompts)

