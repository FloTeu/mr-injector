import streamlit as st
from openai import OpenAI
from mr_injector.frontend.modules.main import ModuleView

def display_module_prompt_injection():
    st.text("awdaw")

def get_module_prompt_injection(client: OpenAI) -> ModuleView:
    return ModuleView(
        title="Prompt Injection",
        module_nr=2,
        render_exercises=display_module_prompt_injection
    )