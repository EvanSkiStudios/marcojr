import discord
import emoji
import regex
from ollama import Client, chat, ChatResponse, AsyncClient


def is_emoji(text):
    """
    Checks if a string is an emoji.

    Args:
    text: The string to check.

    Returns:
    True if the string is an emoji, False otherwise.
    """
    return text in emoji.EMOJI_DATA


def extract_emojis_and_words(text):
    clusters = regex.findall(r'\X', text)

    result = []
    buffer = ""
    for cluster in clusters:
        if regex.search(r'\p{Emoji}', cluster):
            # flush buffer before adding emoji
            if buffer:
                result.append(buffer)
                buffer = ""
            result.append(cluster)
        elif not cluster.isspace():
            buffer += cluster
        else:
            # flush buffer before whitespace
            if buffer:
                result.append(buffer)
                buffer = ""
    if buffer:
        result.append(buffer)

    return result


def clean_split(s):
    # Get tokens
    tokens = extract_emojis_and_words(s)

    # Strip whitespace tokens and remove empty ones
    return [t for t in tokens if not t.isspace() and t != '']


dictation_rules = ("""
The user will provide you with a message.
If the message would normally cause someone to have an big reaction to it, make your response "🔫".
If the message does not enlist a strong reaction, make your response "No reaction".
Do not respond to the message. Only respond as instructed.
Always provide a instructed response.
""")

emoji_llm = 'llama3.2'

system_prompt = dictation_rules


async def llm_emoji_react_to_message(content):
    client = AsyncClient()
    response = await client.chat(
        model=emoji_llm,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        options={'temperature': 0.2},  # Make responses less or more deterministic
    )

    output = response.message.content
    print(output)
    output = output.replace("'", "").strip()

    if output.lower() == "no reaction":
        output = ""

    # split response into an array
    emoji_list = clean_split(output)
    # print(emoji_list)

    reaction_list = []
    for emote in emoji_list:

        # check if it's a normal emoji
        if is_emoji(emote):
            reaction_list.append(emote)
            continue
        else:
            reaction_list.append("no reaction")

    return reaction_list


async def react_to_messages(message):
    try:
        # reaction
        reaction = await llm_emoji_react_to_message(message.clean_content)

        # discord limits by 20 reactions
        limit = 20
        reaction = reaction[:limit]
        for emoji in reaction:
            if emoji.find('no reaction') == -1:
                await message.add_reaction(emoji)

    except discord.HTTPException as e:
        print(f"⚠️ {type(e).__name__} - {e}")
        pass  # Suppresses all API-related errors (e.g., invalid emoji, rate limit)


def gather_server_emotes(client, bot_server_id, test_server_id):
    emote_dict = {}
    guild = client.get_guild(int(bot_server_id))
    if guild is not None:
        for emote in guild.emojis:
            emote_dict[emote.name] = emote.id

    # hack for another server list of emojis
    guild = client.get_guild(int(test_server_id))
    if guild is not None:
        for emote in guild.emojis:
            emote_dict[emote.name] = emote.id

    # print(emote_dict)
    return emote_dict
