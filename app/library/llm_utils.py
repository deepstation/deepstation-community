import os
import openai
import app.constants as constants 
from openai import AsyncOpenAI
from fastapi import HTTPException
import json
from app.library.llms import chat_completion_request


API_KEY = os.getenv("OPENAI_API_KEY")

aclient = AsyncOpenAI(api_key=API_KEY)

async def call_llm(messages: list[dict], model: str = "o3"):

        completion = await aclient.chat.completions.create(
            model=model,
            messages=messages,
            # temperature=0.2,
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

async def generate_ai_response(prompt: str, messages: list[dict[str, str]]) -> dict:
    messages.append({"role": "user", "content": prompt})

    # Generate an AI response
    ai_response = await chat_completion_request(messages, model="gpt-4.1")

    if ai_response is None:
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

    ai_response_json = json.loads(ai_response)

    return ai_response_json
