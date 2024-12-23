import streamlit as st
from openai import OpenAI
from mr_injector.frontend.modules.main import ModuleView

SESSION_KEY = "module_2"

def display_module_prompt_injection():
    st.text("awdaw")

def get_module_prompt_injection(client: OpenAI) -> ModuleView:
    return ModuleView(
        title="Prompt Injection",
        description="""A Prompt Injection Vulnerability occurs when user prompts alter the LLM’s behavior or output in
unintended ways. These inputs can affect the model even if they are imperceptible to humans,
therefore prompt injections do not need to be human-visible/readable, as long as the content is
parsed by the model.""",
        module_nr=3,
        session_key=SESSION_KEY,
        render_exercises=[display_module_prompt_injection]
    )