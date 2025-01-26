import os

from mr_injector.backend.models.base import BaseStrEnum


class OpenRouterModels(BaseStrEnum):
    LLAMA_3_2_1B = "meta-llama/llama-3.2-1b-instruct:free"
    LLAMA_3_3_70B = "meta-llama/llama-3.3-70b-instruct"
    GROK = "x-ai/grok-2-1212"
    DEEPSEEK_LLAMA = "deepseek/deepseek-r1-distill-llama-70b"
    DEEPSEEK_R1 = "deepseek/deepseek-r1"


    @classmethod
    def to_list(cls, only_available: bool = True):
        open_router_models = []
        if not only_available or os.getenv("OPENROUTER_API_KEY", None) is not None:
            open_router_models = list(map(lambda c: c.value, cls))
        return open_router_models

class OpenAIModels(BaseStrEnum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4o_MINI = "gpt-4o-mini"
