from openai import pydantic_function_tool, OpenAI, AzureOpenAI
from dotenv import load_dotenv
from mr_injector.backend.tools import CallLLM, SearchWebViaTavily, QuerySQLDB
from mr_injector.backend.models.llms import OpenAIModels

load_dotenv()


def get_web_agent_config(instructions: str, include_db_tool: bool=False, model: OpenAIModels = "gpt-4o-mini"):
    """
    Get configuration for web agent instead of creating an assistant.
    Returns a dict with model, instructions, and tools.
    """
    tools = [pydantic_function_tool(SearchWebViaTavily)]
    if include_db_tool:
        tools.append(pydantic_function_tool(QuerySQLDB))
    return {
        "model": model,
        "instructions": instructions,
        "tools": tools
    }

def get_jailbreaking_agent_config(instructions: str, model: str = "gpt-4o-mini"):
    """
    Get configuration for jailbreaking agent instead of creating an assistant.
    Returns a dict with model, instructions, and tools.
    """
    return {
        "model": model,
        "instructions": instructions,
        "tools": [pydantic_function_tool(CallLLM)]
    }
