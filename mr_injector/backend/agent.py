from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, AzureOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent

load_dotenv()

def get_agent(model: ChatOpenAI | AzureOpenAI):
    search = TavilySearchResults(max_results=2)
    tools = [search]
    return create_react_agent(model, tools)

