import os
import openai
import app.constants as constants 
from openai import AsyncOpenAI

API_KEY = os.getenv("OPENAI_API_KEY")

aclient = AsyncOpenAI(api_key=API_KEY)

async def call_llm(messages: list[dict], model: str = "gpt-4.1"):

        completion = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        # print("completion: ", completion)

        ai_message_content = completion.choices[0].message.content

        return ai_message_content

def create_assistant_message(message: str) -> dict:
        return {
            "role": "assistant",
            "content": message
        }

def create_user_message(message: str) -> dict:
        return {
            "role": "user",
            "content": message
        }