from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, AzureOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
from langgraph.prebuilt import create_react_agent

load_dotenv()

def get_agent(model: ChatOpenAI | AzureOpenAI, tavily_api_key):
    search = TavilySearchResults(api_wrapper=TavilySearchAPIWrapper(tavily_api_key=tavily_api_key), max_results=2)
    tools = [search]
    return create_react_agent(model, tools)

