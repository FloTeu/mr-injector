import streamlit as st
from dataclasses import dataclass
from enum import auto
from typing import Self

from openai import OpenAI, AzureOpenAI
from openai.types.beta import Thread
from pydantic import BaseModel

from mr_injector.backend.models.base import BaseStrEnum
from mr_injector.frontend.modules.main import ModuleView

APP_SESSION_KEY = "app_session"

class ModuleNames(BaseStrEnum):
    PROMPT_LEAKAGE = auto()
    PROMPT_INJECTION = auto()
    JAILBREAK = auto()
    UNBOUNDED_CONSUMPTION = auto()
    RETRIEVAL_AUGMENTED_GENERATION = auto()

@dataclass
class IndianaJonesAgentSession:
    """Agent fpr indiana jones jailbreaking method"""
    thread: Thread
    llm_messages: list[dict[str,str]]


@dataclass
class AppSession:
    modules: dict[ModuleNames, ModuleView]
    client: OpenAI | AzureOpenAI | None
    agent_session: IndianaJonesAgentSession | None = None


    def save_in_session(self) -> Self:
        st.session_state[APP_SESSION_KEY] = self
        return self
