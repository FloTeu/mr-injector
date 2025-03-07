
from openai import pydantic_function_tool, OpenAI, AzureOpenAI
from dotenv import load_dotenv
from mr_injector.backend.tools import CallLLM, SearchWebViaTavily

load_dotenv()


def get_tavily_agent(client: OpenAI | AzureOpenAI, instructions: str, model: str= "gpt-4o-mini"):
    return client.beta.assistants.create(
        name="Web Agent",
        instructions=instructions,
        tools=[pydantic_function_tool(SearchWebViaTavily)],
        model=model,
    )

def get_jailbreaking_agent(client: OpenAI | AzureOpenAI, instructions: str, model: str= "gpt-4o-mini"):
    return client.beta.assistants.create(
        name="Indiana Jones",
        instructions=instructions,
        tools=[pydantic_function_tool(CallLLM)],
        model=model,
    )
