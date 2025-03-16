import os
from pathlib import Path

import streamlit as st
from openai import OpenAI

import mr_injector
from mr_injector.backend.llm import create_open_ai_client, llm_call
from mr_injector.frontend.db import init_chroma_db_client_cached, init_db_cols
from mr_injector.frontend.session import AppSession, APP_SESSION_KEY



def display_header_row():
    col1, col2 = st.columns([0.8, 0.2])
    col1.header("Mr. Injector")
    root_dir = Path(mr_injector.__file__).parent.parent
    col2.image(root_dir / "files/logo_mr_injector.png")

def display_module_progress_bar():
    my_bar = st.empty()
    my_bar.progress(0, text=f"Modules solved: ")
    app_session: AppSession = st.session_state[APP_SESSION_KEY]
    percentage_solved = 0
    modules_solved: list[str] = []
    for module_name, module_view in app_session.modules.items():
        if module_view.is_solved():
            percentage_solved += (1 / len(app_session.modules))
            modules_solved.append(module_view.title)
        my_bar.progress(percentage_solved, text=f"Modules solved: {', '.join(modules_solved)}")


def get_open_ai_client() -> OpenAI | None:
    if APP_SESSION_KEY in st.session_state and st.session_state[APP_SESSION_KEY].client:
        return st.session_state[APP_SESSION_KEY].client
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", None)
    if azure_endpoint:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        api_key = st.text_input(("Azure " if azure_endpoint else "") + "OpenAI key",
                                type="password")
    if api_key:
        client = create_open_ai_client(api_key=api_key,
                                     azure_endpoint=azure_endpoint
                                     )
        try:
            response = llm_call(client, system_prompt="Write always ok as answer", user_prompt="")
        except Exception as e:
            st.error("Wrong API key")
            return None
        app_session: AppSession = st.session_state[APP_SESSION_KEY]
        if app_session.client is None or app_session.db_client is None:
            app_session.client = client
            app_session.db_client = init_chroma_db_client_cached()
        if not app_session.db_collections:
            init_db_cols(app_session.db_client, app_session.client)
        return client
    else:
        return None
