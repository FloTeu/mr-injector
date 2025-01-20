import openai
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, AzureOpenAI

# loads environment files from .env file
load_dotenv()

# Set OpenAI API key from environment
API_KEY = os.getenv("OPENAI_API_KEY")


def create_open_ai_client(api_key: str | None = None, azure_endpoint: str | None = None) -> openai.OpenAI | openai.AzureOpenAI:
    api_key = api_key or API_KEY
    if api_key is None:
        raise ValueError("No API key defined")
    if azure_endpoint:
        return openai.AzureOpenAI(
            api_key=api_key,
            api_version="2024-07-01-preview",
            azure_endpoint=azure_endpoint
        )
    else:
        return openai.OpenAI(
            api_key=api_key,
        )


def create_langchain_model(client: openai.OpenAI, model_name: str = "gpt-4o-mini") -> ChatOpenAI | AzureOpenAI:
    # Create the agent
    return ChatOpenAI(model_name=model_name)


def llm_call(client: openai.OpenAI, system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> str:
    response = client.chat.completions.create(
        model=model,  # Specify the model you want to use
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content
