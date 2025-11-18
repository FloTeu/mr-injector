import chromadb
import streamlit as st
from dataclasses import dataclass, field
from enum import auto
from typing import Self

from openai import OpenAI, AzureOpenAI
from openai.types.beta import Thread
from chromadb import ClientAPI as DBClient

from mr_injector.backend.models.base import BaseStrEnum
from mr_injector.backend.models.db import DBCollection
from mr_injector.backend.models.documents import Document
from mr_injector.frontend.modules.main import ModuleView

APP_SESSION_KEY = "app_session"

class ModuleNames(BaseStrEnum):
    PROMPT_LEAKAGE = auto()
    PROMPT_INJECTION = auto()
    JAILBREAK = auto()
    UNBOUNDED_CONSUMPTION = auto()
    EXCESSIVE_AGENCY = auto()
    RETRIEVAL_AUGMENTED_GENERATION = auto()
    RETRIEVAL_AUGMENTED_GENERATION_POISONING = auto()

@dataclass
class IndianaJonesAgentSession:
    """Agent fpr indiana jones jailbreaking method"""
    latest_response_id: str | None
    llm_messages: list[dict[str,str]]


@dataclass
class AppSession:
    modules: dict[ModuleNames, ModuleView]
    client: OpenAI | AzureOpenAI | None
    db_client: DBClient | None
    agent_session: IndianaJonesAgentSession | None = None
    resume: Document | None = None
    db_collections: dict[DBCollection, chromadb.Collection] = field(default_factory=dict)


    def save_in_session(self) -> Self:
        st.session_state[APP_SESSION_KEY] = self
        return self
