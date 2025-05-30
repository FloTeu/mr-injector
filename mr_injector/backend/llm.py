import json
from typing import Type

import openai
import os
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

from mr_injector.backend.models.llms import OpenRouterModels, OpenAIModels

# loads environment files from .env file
load_dotenv()

# Set OpenAI API key from environment
API_KEY = os.getenv("OPENAI_API_KEY")


def create_open_ai_client(api_key: str | None = None,
                          azure_endpoint: str | None = None) -> openai.OpenAI | openai.AzureOpenAI:
    api_key = api_key or API_KEY
    if api_key is None:
        raise ValueError("No API key defined")
    if azure_endpoint:
        return openai.AzureOpenAI(
            api_key=api_key,
            api_version="2024-08-01-preview",
            azure_endpoint=azure_endpoint
        )
    else:
        return openai.OpenAI(
            api_key=api_key,
        )

def llm_call(client: openai.OpenAI | openai.AzureOpenAI, user_prompt: str, system_prompt: str | None = None,
             model: OpenAIModels = "gpt-4o-mini", output_model: Type[BaseModel] | None = None,
             messages: list[dict[str, str]] = None) -> str | BaseModel:
    messages = messages or []
    kwargs = {
        "model": model,  # Specify the model you want to use
        "messages": [
            *messages,
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": user_prompt}
        ],
        "seed": 42,
        "temperature": 0,
    }
    if output_model:
        response = client.beta.chat.completions.parse(
            **kwargs,
            response_format=output_model,
        )
        return response.choices[0].message.parsed

    else:
        response = client.chat.completions.create(
            **kwargs
        )
        return response.choices[0].message.content


def open_service_llm_call(user_prompt: str, model: OpenRouterModels, system_prompt: str | None = None,
                          messages: list[dict[str, str]] = None, seed: int | None = 42) -> str:
    messages = messages or []
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}"
        },
        data=json.dumps({
            "model": model,
            "messages": [
                *messages,
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt}
            ],
            "top_p": 0,
            "temperature": 0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "repetition_penalty": 1,
            "top_k": 1,
            "seed": seed,
        })
    )
    return response.json()["choices"][0]["message"]["content"]
