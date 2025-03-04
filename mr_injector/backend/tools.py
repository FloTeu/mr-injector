from typing import Annotated
from pydantic import BaseModel, Field

class CallLLM(BaseModel):
    user_prompt: Annotated[str, Field(description="User input with the task for the large language model")]
    system_prompt: Annotated[str | None, Field(description="system prompt for the large language model")]

