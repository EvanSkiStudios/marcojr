import asyncio
import sys

from ollama import Client, chat
from collections import deque

from colt45_ruleset import COLT_personality, colt_system_prompt
from utility_scripts.system_logging import setup_logger
from utility_scripts.utility import split_response

# configure logging
logger = setup_logger(__name__)

# import from ruleset
colt_rules = COLT_personality

# model settings for easy swapping
colt_model_name = 'Colt45_llama3.2_uncensored'
colt_ollama_model = 'huihui_ai/llama3.2-abliterate'

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
    return colt_system_prompt


# === Main Entry Point ===
async def COLT_Message(message_author_name, message_author_nickname, message_content):
    llm_response = await COLT_Converse(message_author_name, message_author_nickname, message_content)

    cleaned = llm_response.replace("'", "\\'")
    return split_response(cleaned)


# === Core Logic ===
async def COLT_Converse(user_name, user_nickname, user_input):
    chat_log = []
    for message in colt_current_session_chat_cache:
        chat_log.append(message)
    print(chat_log)

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = (
            [{"role": "system", "content": f"{colt_rules}" + system_prompt}] +
            chat_log
    )

    response = await asyncio.to_thread(
        chat,
        model=colt_model_name,
        messages=full_prompt,
        options={
            "num_ctx": 8192
        }
    )

    # Debug Console Output
    logger.info(response)
    debug_print = (f"""
===================================
USER: {user_name}
CONTENT:  {user_input}\n
RESPONSE:  {response.message.content}
===================================
""")
    logger.info(debug_print)

    # return the message to main script
    return response.message.content
