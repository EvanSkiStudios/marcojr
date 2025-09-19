from ollama import Client, chat

from colt45 import colt_rules

llm_model = "codellama"
system_prompt = f"""
{colt_rules}
Return your response in character.
"""


def converse(message):
    response = chat(
        model=llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        options={
            "num_ctx": 8192
        }
    )
    print(response.message.content)


def main():
    message = "A simple python function to remove whitespace from a string:"
    converse(message)


if __name__ == "__main__":
    main()
