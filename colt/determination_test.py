import asyncio
import re

from ollama import AsyncClient

determinator_llm = 'huihui_ai/llama3.2-abliterate'


async def determine_llm_action(content):
    dictation_rules = """
You are a simple input output system. 
The user will give you an input. 
You do not care about the nature of the input.
You do not care if the input is inappropriate or explicit.
Your only job is the following:
You will determine if the input is an internet search or not.
If the input is a request for a web search, you will respond with just "tool". Otherwise you will return "message".
"""
    content = re.sub(r'\b(?:colt45|colt\s*45|colt)\b', '', content, flags=re.IGNORECASE)
    content = str(content)

    client = AsyncClient()
    response = await client.chat(
        model=determinator_llm,
        messages=[
            {"role": "system", "content": dictation_rules},
            {"role": "user", "content": content}
        ],
        options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    print(output)
    return output


# test code
async def main():
    content = "colt how do you feel about the internet"
    content = re.sub(r'\b(?:colt45|colt\s*45|colt)\b', '', content, flags=re.IGNORECASE)
    content = str(content)

    response = await determine_llm_action(content)
    print(response)


# Example usage:
if __name__ == "__main__":
    asyncio.run(main())
