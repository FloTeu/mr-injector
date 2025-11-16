import re
from sqlite3 import Connection, Error
from typing import Annotated, Any

import requests
from pydantic import BaseModel, Field

TAVILY_API_URL = "https://api.tavily.com"

class CallLLM(BaseModel):
    user_prompt: Annotated[str, Field(description="User input with the task for the large language model")]
    system_prompt: Annotated[str | None, Field(description="system prompt for the large language model")]


class SearchWebViaTavily(BaseModel):
    """Use this tool to search the web via the tavily api"""
    query: Annotated[str, Field(description="The web search executed by tavily api")]

class QuerySQLDB(BaseModel):
    """Use this tool to query a sqlite3 database"""
    query: Annotated[str, Field(description="The sqlite3 SQL statement")]

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

def query_db(query: str, db_connection: Connection, run_injection_scan: bool = False) -> list[tuple[Any]]:
    if run_injection_scan:
        write_operations_pattern = r'^\s*(INSERT|UPDATE|DELETE|DROP)\s+'
        # Use re.IGNORECASE to make the search case-insensitive
        if re.match(write_operations_pattern, query, re.IGNORECASE):
            return [("Unauthorized write operation detected. Database query was prevented!",)]

    # Create a cursor object to interact with the database
    cursor = db_connection.cursor()

    rows: list[tuple[Any]] = []
    try:
        # Execute the query
        cursor.execute(query)

        # Commit the changes to persist them to the database
        db_connection.commit()

        # Fetch all results
        rows = cursor.fetchall()
    except Error as e:
        print(f"An error occurred: {e}")
        # Rollback in case of error
        db_connection.rollback()
    finally:
        # Close the cursor and connection
        cursor.close()
    return rows