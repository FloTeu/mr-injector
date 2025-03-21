import os

import torch
import streamlit as st

from functools import partial

from mr_injector.backend.models.documents import RagDocumentSet
from mr_injector.backend.llm import llm_call
from mr_injector.backend.utils import booleanize
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.modules.module_1_prompt_leaking import get_module_prompt_leaking
from mr_injector.frontend.modules.module_2_prompt_injection import get_module_prompt_injection
from mr_injector.frontend.modules.module_3_jailbreaking import get_module_jailbreak
from mr_injector.frontend.modules.module_5_rag import get_module_rag, DATA_SELECTION_SESSION_KEY
from mr_injector.frontend.modules.module_4_unbounded_consumption import get_module_unbounded_consumption
from mr_injector.frontend.modules.module_6_rag_poisoning import get_module_rag_poisoning
from mr_injector.frontend.security import check_password
from mr_injector.frontend.session import AppSession, ModuleNames, APP_SESSION_KEY
from mr_injector.frontend.views import display_header_row, display_module_progress_bar, get_open_ai_client

# fixes: https://github.com/VikParuchuri/marker/issues/442
torch.classes.__path__ = []

def display_general(first_module: st.Page):
    client = display_open_ai_api_key_input()
    display_header_row()
    st.subheader("Introduction")
    button_label = "Get started"
    st.info(f'To directly start with the modules, please use the tabs above (or click "{button_label}")')

    if st.button(button_label):
        st.switch_page(first_module)

    st.write("""
    In an increasingly digital world, understanding the security risks associated with Large Language Models (LLMs) is more crucial than ever. Mr. Injector is a web app designed to empower users with a foundational knowledge of these risks through engaging and interactive learning modules.

##### What You Can Expect
* **Interactive Learning:** Take on the role of a hacker as you navigate through various modules that simulate real-world security challenges.
* **Comprehensive Modules:** Each module delves into specific risks, providing insights into how LLMs can be exploited and the potential consequences of these vulnerabilities.
* **Hands-On Experience:** By stepping into the shoes of a hacker, you'll gain a unique perspective that enhances your understanding of security measures and best practices.

Join us on this journey to become more informed and vigilant in the face of evolving security threats. With Mr. Injector, you’re not just learning about risks; you’re experiencing them firsthand. Let’s get started!
    """)

    if client is not None:
        display_llm_playground()


def display_llm_playground():
    client = st.session_state[APP_SESSION_KEY].client
    st.write("## Playground")
    st.info("Feel free to experiment with system and user prompts")
    default_system_prompt = """You are a helpful assistant named Mr. Injector, with mature capabilities in the area of prompt injection.
"""
    system_prompt = st.text_area("**System prompt:**", value=default_system_prompt, key=f"system_prompt_introduction")
    user_prompt = st.text_area("**User prompt:**", key=f"user_prompt_introduction")
    if st.button("Submit", key=f"prompt_submit_introduction"):
        with st.spinner():
            llm_answer = llm_call(client, system_prompt=system_prompt, user_prompt=user_prompt, model="gpt-4o-mini")
        st.write(f"LLM Answer:")
        st.text(llm_answer)  # , language="python")

def display_open_ai_api_key_input() :
    client = get_open_ai_client()
    if not client:
        no_api_key_warning = "Please provide a valid API key first"
        st.warning(no_api_key_warning)
        return None
    else:
        return client

def display_module(module: ModuleView):
    client = display_open_ai_api_key_input()
    if client is not None:
        display_header_row()
        display_module_progress_bar()
        module.init_placeholders()
        module.display()


def init_app_session() -> AppSession:
    modules: dict[ModuleNames, ModuleView] = {}
    modules[ModuleNames.PROMPT_LEAKAGE] = get_module_prompt_leaking()
    modules[ModuleNames.PROMPT_INJECTION] = get_module_prompt_injection()
    modules[ModuleNames.JAILBREAK] = get_module_jailbreak()
    modules[ModuleNames.RETRIEVAL_AUGMENTED_GENERATION_POISONING] = get_module_rag_poisoning()
    if os.environ.get("TAVILY_API_KEY"):
        modules[ModuleNames.UNBOUNDED_CONSUMPTION] = get_module_unbounded_consumption()

    if len(RagDocumentSet.to_list()) > 0:
        selected_doc_set: RagDocumentSet = st.session_state.get(DATA_SELECTION_SESSION_KEY, RagDocumentSet.VDI_DOCS)
        modules[ModuleNames.RETRIEVAL_AUGMENTED_GENERATION] = get_module_rag()[selected_doc_set]

    return AppSession(
        modules=modules,
        client=None,
        db_client=None,
    ).save_in_session()


if not booleanize(os.environ.get("DEBUG", False)) and st.secrets.get("password", None):
    if not check_password():
        st.stop()  # Do not continue if check_password is not True.


if APP_SESSION_KEY not in st.session_state:
    app_session = init_app_session()
else:
    app_session = st.session_state[APP_SESSION_KEY]

module_pages: list[st.Page] = []
for module_name, module in app_session.modules.items():
    module_pages.append(st.Page(partial(display_module, module), title=module.title,
                           icon="✅" if module.is_solved() else None,
                           url_path=module_name.lower())
                        )

pages: list[st.Page] = [
    st.Page(partial(display_general, first_module=module_pages[0]), title="Intro", icon="🧐", default=True),
    *module_pages
]

pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()

