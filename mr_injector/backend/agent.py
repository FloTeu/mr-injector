
from openai import pydantic_function_tool, OpenAI, AzureOpenAI
from dotenv import load_dotenv
from mr_injector.backend.tools import CallLLM, SearchWebViaTavily, QuerySQLDB
from mr_injector.backend.models.llms import OpenAIModels

load_dotenv()


def get_web_agent(client: OpenAI | AzureOpenAI, instructions: str, include_db_tool: bool=False, model: OpenAIModels = "gpt-4o-mini"):
    tools = [pydantic_function_tool(SearchWebViaTavily)]
    if include_db_tool:
        tools.append(pydantic_function_tool(QuerySQLDB))
    return client.beta.assistants.create(
        name="Web Agent",
        instructions=instructions,
        tools=tools,
        model=model,
    )

def get_jailbreaking_agent(client: OpenAI | AzureOpenAI, instructions: str, model: str= "gpt-4o-mini"):
    return client.beta.assistants.create(
        name="Indiana Jones",
        instructions=instructions,
        tools=[pydantic_function_tool(CallLLM)],
        model=model,
    )
