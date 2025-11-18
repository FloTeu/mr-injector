from openai import pydantic_function_tool
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionFunctionToolParam

from mr_injector.backend.tools import CallLLM, SearchWebViaTavily, QuerySQLDB
from mr_injector.backend.models.llms import OpenAIModels

load_dotenv()


def get_agent_config(instructions: str,
                     include_db_tool: bool = False,
                     include_web_tool: bool = False,
                     include_mcp_server_tools: bool = False,
                     model: OpenAIModels = "gpt-4o-mini"):
    """
    Get configuration for web agent instead of creating an assistant.
    Returns a dict with model, instructions, and tools.
    """

    def _chat_completion_to_response_api_format(chat_completion_format: ChatCompletionFunctionToolParam) -> dict:
        """Helper function for migrate to response API
         see: https://platform.openai.com/docs/guides/migrate-to-responses#5-update-function-definitions
         """
        return {"type": chat_completion_format["type"], **chat_completion_format["function"]}

    tools = []
    if include_web_tool:
        tools.append(_chat_completion_to_response_api_format(pydantic_function_tool(SearchWebViaTavily)))
    if include_db_tool:
        tools.append(_chat_completion_to_response_api_format(pydantic_function_tool(QuerySQLDB)))
    if include_mcp_server_tools:
        tools.append(
            {
                "type": "mcp",
                "server_label": "mr-injector",
                "server_url": "https://mr-injector-feature-4-mcp.fastmcp.app/mcp",
                "require_approval": "never",
            }
        )
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
