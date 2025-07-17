import os
from tenacity import (
    retry,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from termcolor import colored
from openai import AsyncOpenAI
from openai import OpenAIError

import logging

API_KEY = os.getenv("OPENAI_API_KEY")

aclient = AsyncOpenAI(api_key=API_KEY)

logger = logging.getLogger(__name__)


@retry(
    wait=wait_random_exponential(multiplier=1, max=1),
    stop=stop_after_attempt(1),
    retry=retry_if_exception_type(OpenAIError),  # Only retry OpenAI-related errors
)
async def chat_completion_request(
    messages, tools=None, tool_choice=None, model="gpt-4o"
):
    try:
        completion = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            # temperature=0.2,
            response_format={"type": "json_object"},
        )

        print("completion: ", completion)

        ai_message_content = completion.choices[0].message.content

        return ai_message_content
    except Exception as e:
        print("error: ", e)
        logger.error(f"Error in chat_completion_request: {e}")
        raise e


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function": "magenta",
    }

    for message in messages:
        if message["role"] == "system":
            print(
                colored(
                    f"system: {message['content']}\n", role_to_color[message["role"]]
                )
            )
        elif message["role"] == "user":
            print(
                colored(f"user: {message['content']}\n", role_to_color[message["role"]])
            )
        elif message["role"] == "assistant" and message.get("function_call"):
            print(
                colored(
                    f"assistant: {message['function_call']}\n",
                    role_to_color[message["role"]],
                )
            )
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(
                colored(
                    f"assistant: {message['content']}\n", role_to_color[message["role"]]
                )
            )
        elif message["role"] == "function":
            print(
                colored(
                    f"function ({message['name']}): {message['content']}\n",
                    role_to_color[message["role"]],
                )
            )
