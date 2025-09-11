import asyncio
import re

from ollama import ChatResponse, chat

import colt45_ruleset
from tools.web_search.google_websearch import google_search
from utility_scripts.utility import split_response

search_model = 'llama3.2'
chat_model = 'llama3.2'


def search_the_web(query):
    return google_search(query)


available_functions = {
    'search_the_web': search_the_web,
}

system_prompt = f"""
{colt45_ruleset.COLT_personality}
You will be given a list of results from a google search.
Make sure to include the url's of the results in your response.
Put url's inside of <>
For example <(url here)>
"""


async def llm_internet_search(message):
    messages = [
        {'role': 'user', 'content': message}
    ]
    response: ChatResponse = await asyncio.to_thread(
        chat,
        search_model,
        messages=messages,
        # tools=[search_the_web, search_wikipedia],
        tools=[search_the_web],
        options={'temperature': 0.2},  # Make responses less or more deterministic
        stream=False
    )

    if response.message.tool_calls:
        # There may be multiple tool calls in the response
        for tool in response.message.tool_calls:
            # Ensure the function is available, and then call it
            if function_to_call := available_functions.get(tool.function.name):
                print('Calling function:', tool.function.name)
                print('Arguments:', tool.function.arguments)
                output = function_to_call(**tool.function.arguments)
                print('Function output:', output)
            else:
                print('Function', tool.function.name, 'not found')

    # Only needed to chat with the model using the tool call results
    if response.message.tool_calls:
        # Add the function response to messages for the model to use
        messages.append(response.message)
        messages.append({'role': 'tool', 'content': str(output), 'tool_name': tool.function.name})

        # Get final response from model with function outputs
        final_response = chat(chat_model, stream=False, messages=[{'role': 'system', 'content': system_prompt}] + messages)
        # print('Final response:', final_response.message.content)
    else:
        # print('No tool calls returned from model')
        final_response = chat(chat_model, stream=False, messages=[{'role': 'system', 'content': system_prompt}] + messages)
        #print(response)

    output = final_response.message.content
    output = re.sub(r'\bEvanski_\b', 'Evanski', output, flags=re.IGNORECASE)

    print(output)
    return split_response(output)
