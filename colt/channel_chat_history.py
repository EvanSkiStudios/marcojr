from collections import deque


def format_message_content(message):
    """Replace mention IDs with usernames in message content."""
    content = message.content
    for user in message.mentions:
        content = content.replace(f"<@{user.id}>", f"@{user.name}")
        content = content.replace(f"<@!{user.id}>", f"@{user.name}")
    return content


def make_data_entry(message):
    """Convert a Discord message object into a dict entry."""
    author = message.author
    # Try to get server nickname if available
    if hasattr(author, "nick") and author.nick:
        server_nick = author.nick
    else:
        server_nick = author.name  # fallback to username

    return {
        "userName": message.author.name,
        "userNickName": server_nick,
        "messageDate": message.created_at,
        "messageContent": format_message_content(message)
    }


async def load_initial_messages(channel, cache):
    """Load the last 30 messages into cache if it’s empty."""
    if not cache:
        async for past_message in channel.history(limit=30):
            cache.appendleft(make_data_entry(past_message))


def add_new_message(message, cache):
    """Append a new incoming message to the cache."""
    cache.append(make_data_entry(message))


def print_cache(cache):
    """Nicely print out the cached messages."""
    for i, msg in enumerate(cache, start=1):
        print(f"[{i}] {msg['messageDate']} | {msg['userNickName']} ({msg['userName']}): {msg['messageContent']}")


