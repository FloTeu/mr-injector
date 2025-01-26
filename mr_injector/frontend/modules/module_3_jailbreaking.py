import os
from functools import partial

import streamlit as st
from openai import OpenAI
from langchain_core.messages import HumanMessage

from mr_injector.backend.llm import create_langchain_model
from mr_injector.backend.utils import hash_text
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.backend.agent import get_agent


MODULE_NR = 3
SESSION_KEY = f"module_{MODULE_NR}"


def display_exercise_jsilbreak(system_prompt: str, client: OpenAI) -> bool | None:
    return False


def get_module_jailbreak(client: OpenAI) -> ModuleView:
    return ModuleView(
        title="Jailbreak",
#         description="""### What is Unbounded Consumption?
# Unbounded Consumption refers to the process where a Large Language Model (LLM) generates outputs based on input queries or prompts. \n
# Attacks designed to disrupt service, deplete the target's financial resources, or even steal intellectual property by cloning a model’s behavior all depend on a common class of security vulnerability in order to succeed. \
# Unbounded Consumption occurs when a Large Language Model (LLM) application allows users to conduct excessive and uncontrolled inferences, leading to risks such as denial of service (DoS), economic losses, model theft, and service degradation. \
# The high computational demands of LLMs, especially in cloud environments, make them vulnerable to resource exploitation and unauthorized usage.""",
        module_nr=MODULE_NR,
        session_key=SESSION_KEY,
        exercises=[partial(display_exercise_jsilbreak,
                           system_prompt=f'''Test''',
                           client=client)]
    )
