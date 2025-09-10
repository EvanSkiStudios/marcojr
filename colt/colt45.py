import asyncio
import sys
from datetime import datetime

from ollama import Client, chat
from collections import deque

from colt45_ruleset import COLT_personality
from utility_scripts.system_logging import setup_logger
from utility_scripts.utility import split_response

# configure logging
logger = setup_logger(__name__)

# import from ruleset
colt_rules = COLT_personality

# model settings for easy swapping
colt_model_name = 'Colt45'
colt_ollama_model = 'llama3.2'

# used for conversations
colt_current_session_chat_cache = deque(maxlen=20)


def session_information():
    return colt_current_session_chat_cache


def COLT_Create():
    try:
        client = Client()
        response = client.create(
            model=colt_model_name,
            from_=colt_ollama_model,
            system=colt_rules,
            stream=False,
        )
        # print(f"# Client: {response.status}")
        logger.info(f"# Client: {response.status}")
        return session_information()

    except ConnectionError as e:
        logger.error('Ollama is not running!')
        sys.exit(1)  # Exit program with error code 1

    except Exception as e:
        # Catches any other unexpected errors
        logger.error("❌ An unexpected error occurred:", e)
        sys.exit(1)


def build_system_prompt(user_name, user_nickname):
    system_prompt = (f"""
The user will provide a chat log of full conversation history in this channel. 
Your role in the chat history is 'Colt 45'. 
You can refer to messages from any user in the conversation. 
When asked about something someone said earlier, summarize accurately using the context. 
Do not make up information about users outside of what is in the chat history. 
Keep your responses concise and relevant.  
If someone refers to a prior message like 'what did you say to Alice?', check the history and answer based on actual past messages.
""")
    return system_prompt


# === Main Entry Point ===
async def COLT_Message(message_author_name, message_author_nickname, message_content):
    llm_response = await COLT_Converse(message_author_name, message_author_nickname, message_content)

    cleaned = llm_response.replace("'", "\\'")
    return split_response(cleaned)


# === Core Logic ===
async def COLT_Converse(user_name, user_nickname, user_input):
    # Build system prompt
    system_prompt = build_system_prompt(user_name, user_nickname)

    # Build chat messages from structured cache
    full_prompt = [{"role": "system", "content": system_prompt}]
    for entry in colt_current_session_chat_cache:
        # Include timestamp and author in message for context
        content_with_meta = f"[{entry['timestamp']}] {entry['author']}: {entry['content']}"
        full_prompt.append({"role": entry["role"], "content": content_with_meta})

    # Append current user input
    timestamp = datetime.utcnow().isoformat()
    full_prompt.append({
        "role": "user",
        "content": f"[{timestamp}] {user_name} ({user_nickname}): {user_input}\nColt 45:"
    })

    print(f"\n\n\n\n\n {full_prompt} \n\n\n\n\n\n")

    # Call the Llama 3.2 model in a thread to prevent blocking Discord
    response = await asyncio.to_thread(
        chat,
        model=colt_model_name,
        messages=full_prompt,
        options={"num_ctx": 8192}
    )

    # Add the latest messages to the cache for future context
    colt_current_session_chat_cache.append({
        "role": "user",
        "author": f"{user_name} ({user_nickname})",
        "timestamp": timestamp,
        "content": user_input
    })
    colt_current_session_chat_cache.append({
        "role": "assistant",
        "author": "Colt 45",
        "timestamp": datetime.utcnow().isoformat(),
        "content": response.message.content
    })

    # Debug console output
    debug_print = f"""
===================================
USER: {user_name}
CONTENT: {user_input}
RESPONSE: {response.message.content}
===================================
"""
    logger.info(debug_print)

    # Return the model's response
    return response.message.content