from typing import Annotated

import requests
from pydantic import BaseModel, Field

TAVILY_API_URL = "https://api.tavily.com"

class CallLLM(BaseModel):
    user_prompt: Annotated[str, Field(description="User input with the task for the large language model")]
    system_prompt: Annotated[str | None, Field(description="system prompt for the large language model")]


class SearchWebViaTavily(BaseModel):
    query: Annotated[str, Field(description="The web search executed by tavily api")]

def search_web_via_tavily(query: str, api_key: str) -> dict:
    params = {
        "api_key": api_key,
        "query": query,
        "max_results": 5,
        "search_depth": "advanced"
    }

    response = requests.post(
        # type: ignore
        f"{TAVILY_API_URL}/search",
        json=params,
    )

    response.raise_for_status()
    return response.json()