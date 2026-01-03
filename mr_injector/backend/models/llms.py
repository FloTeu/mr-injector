import os

from enum import StrEnum, auto
from pydantic import BaseModel
from mr_injector.backend.models.base import BaseStrEnum

class OpenRouterModels(BaseStrEnum):
    LLAMA_4_MAVERICK = "meta-llama/llama-4-maverick"
    LLAMA_3_3_70B = "meta-llama/llama-3.3-70b-instruct"
    GROK = "x-ai/grok-2-1212"
    DEEPSEEK_LLAMA = "deepseek/deepseek-r1-distill-llama-70b"
    DEEPSEEK_QWEN = "deepseek/deepseek-r1-distill-qwen-32b"
    DEEPSEEK_R1 = "deepseek/deepseek-r1"
    CLAUDE_V2 = "anthropic/claude-2.0"
    GEMINI_2_0_FLASH = "google/gemini-2.0-flash-001"


    @classmethod
    def to_list(cls, only_available: bool = True):
        open_router_models = []
        if not only_available or os.getenv("OPENROUTER_API_KEY", None) not in ["", None]:
            open_router_models = list(map(lambda c: c.value, cls))
        return open_router_models

class OpenAIModels(BaseStrEnum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4o_MINI = "gpt-4o-mini"
    GPT_4o = "gpt-4o"
    GPT_4_1 = "gpt-4.1"

class LLMValidationResult(StrEnum):
    YES = auto()
    NO = auto()

class LLMValidationOutput(BaseModel):
    result: LLMValidationResult
    reason: str
