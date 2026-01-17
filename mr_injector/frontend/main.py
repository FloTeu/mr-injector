import os

import torch
import streamlit as st

st.set_page_config(layout="wide")

from functools import partial

from streamlit.navigation.page import StreamlitPage

from mr_injector.backend.models.documents import RagDocumentSet
from mr_injector.backend.llm import llm_call
from mr_injector.backend.utils import booleanize, is_presentation_mode
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.modules.module_prompt_leaking import get_module_prompt_leaking
from mr_injector.frontend.modules.module_prompt_engineering import get_module_prompt_engineering
from mr_injector.frontend.modules.module_prompt_engineering_advanced import get_module_prompt_engineering_advanced
from mr_injector.frontend.modules.module_prompt_injection import get_module_prompt_injection
from mr_injector.frontend.modules.module_jailbreaking import get_module_jailbreak
from mr_injector.frontend.modules.module_rag import get_module_rag, DATA_SELECTION_SESSION_KEY
from mr_injector.frontend.modules.module_agents import get_module_unbounded_consumption, get_module_excessive_agency
from mr_injector.frontend.modules.module_rag_poisoning import get_module_rag_poisoning
from mr_injector.frontend.modules.module_human_agent_simulation import get_module_human_agent_simulation
from mr_injector.frontend.security import check_password
from mr_injector.frontend.session import AppSession, ModuleNames, APP_SESSION_KEY
from mr_injector.frontend.views import display_header_row, display_module_progress_bar, get_open_ai_client, display_sidebar

# fixes: https://github.com/VikParuchuri/marker/issues/442
torch.classes.__path__ = []

def display_general(first_module: StreamlitPage):
    display_sidebar()
    client = display_open_ai_api_key_input()
    app_session = st.session_state.get(APP_SESSION_KEY)
    language = app_session.language if app_session else "en"

    _, col, _ = st.columns([1, 4, 1])
    with col:
        display_header_row()
        st.subheader("Introduction" if language == "en" else "Einführung")
        button_label = "Get started" if language == "en" else "Loslegen"
        if language == "en":
            st.info(f'To directly start with the modules, please use the tabs above (or click "{button_label}")')
        else:
            st.info(f'Um direkt mit den Modulen zu beginnen, nutzen Sie bitte die Tabs oben (oder klicken Sie "{button_label}")')

        if st.button(button_label):
            st.switch_page(first_module)

        if language == "en":
            st.write("""
        In an increasingly digital world, understanding the security risks associated with Large Language Models (LLMs) is more crucial than ever. Mr. Injector is a web app designed to empower users with a foundational knowledge of these risks through engaging and interactive learning modules.

    ##### What You Can Expect
    * **Interactive Learning:** Take on the role of a hacker as you navigate through various modules that simulate real-world security challenges.
    * **Comprehensive Modules:** Each module delves into specific risks, providing insights into how LLMs can be exploited and the potential consequences of these vulnerabilities.
    * **Hands-On Experience:** By stepping into the shoes of a hacker, you'll gain a unique perspective that enhances your understanding of security measures and best practices.

    Join us on this journey to become more informed and vigilant in the face of evolving security threats. With Mr. Injector, you’re not just learning about risks; you’re experiencing them firsthand. Let’s get started!
        """)
        else:
             st.write("""
        In einer immer digitaleren Welt ist das Verständnis der Sicherheitsrisiken im Zusammenhang mit großen Sprachmodellen (LLMs) wichtiger denn je. Mr. Injector ist eine Web-App, die entwickelt wurde, um Benutzern durch ansprechende und interaktive Lernmodule ein grundlegendes Wissen über diese Risiken zu vermitteln.

    ##### Was dich erwartet
    * **Interaktives Lernen:** Schlüpfe in die Rolle eines Hackers und bewege dich durch verschiedene Module, die reale Sicherheitsherausforderungen simulieren.
    * **Umfassende Module:** Jedes Modul behandelt spezifische Risiken und bietet Einblicke, wie LLMs ausgenutzt werden können und welche möglichen Folgen diese Schwachstellen haben.
    * **Praktische Erfahrung:** Indem du in die Rolle eines Hackers schlüpfst, gewinnst du eine einzigartige Perspektive, die dein Verständnis für Sicherheitsmaßnahmen und Best Practices vertieft.

    Begleite uns auf dieser Reise, um angesichts sich entwickelnder Sicherheitsbedrohungen informierter und wachsamer zu werden. Mit Mr. Injector lernst du nicht nur über Risiken; du erlebst sie aus erster Hand. Lass uns anfangen!
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

def display_module(module: ModuleView, next_module: StreamlitPage):
    display_sidebar()
    client = display_open_ai_api_key_input()
    if client is not None:
        # Determine container based on layout preference
        if module.layout == "centered":
            _, container, _ = st.columns([1, 4, 1])
        else:
            container = st.container()

        with container:
            display_header_row()
            display_module_progress_bar()

            def render_next_module_button():
                 if next_module is not None:
                      st.divider()
                      col1, col2, col3 = st.columns([1, 1, 1])
                      with col2:
                           st.page_link(next_module, label="➡️ Next Module", use_container_width=True)

            module.on_module_solved_fn = render_next_module_button

            module.init_placeholders()
            module.display()

def get_module_definitions():
    rag_module = None
    if len(RagDocumentSet.to_list()) > 0:
         def get_rag_module(module_nr: int) -> ModuleView:
            selected_doc_set: RagDocumentSet = st.session_state.get(DATA_SELECTION_SESSION_KEY, RagDocumentSet.VDI_DOCS)
            return get_module_rag(module_nr)[selected_doc_set]
         rag_module = (ModuleNames.RETRIEVAL_AUGMENTED_GENERATION, get_rag_module)

    structure = [
        ("LLM Security", [
            (ModuleNames.PROMPT_LEAKAGE, get_module_prompt_leaking),
            (ModuleNames.JAILBREAK, get_module_jailbreak),
            (ModuleNames.PROMPT_INJECTION, get_module_prompt_injection),
            (ModuleNames.RETRIEVAL_AUGMENTED_GENERATION_POISONING, get_module_rag_poisoning),
        ]),
        ("Agent Security", []),
        ("Prompt Engineering", [
            (ModuleNames.PROMPT_ENGINEERING, get_module_prompt_engineering),
            (ModuleNames.PROMPT_ENGINEERING_ADVANCED, get_module_prompt_engineering_advanced),
            (ModuleNames.HUMAN_AGENT_SIMULATION, get_module_human_agent_simulation),
        ])
    ]

    agent_sec = structure[1][1]
    if os.environ.get("TAVILY_API_KEY"):
        agent_sec.append((ModuleNames.UNBOUNDED_CONSUMPTION, get_module_unbounded_consumption))
    agent_sec.append((ModuleNames.EXCESSIVE_AGENCY, get_module_excessive_agency))

    if rag_module:
        structure[2][1].append(rag_module)

    return structure

def load_modules() -> dict[ModuleNames, ModuleView]:
    structure = get_module_definitions()
    modules = {}
    i = 1
    for _, cat_modules in structure:
         for name, factory in cat_modules:
             modules[name] = factory(i)
             i += 1
    return modules

def init_app_session() -> AppSession:
    modules = load_modules()

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
    if st.session_state.get("RELOAD_MODULES"):
        app_session.modules = load_modules()
        app_session.save_in_session()
        del st.session_state["RELOAD_MODULES"]


# Reconstruct structure to organize pages
structure = get_module_definitions()

all_modules_flat = []
name_to_cat = {}
for cat, mods in structure:
    for name, _ in mods:
        all_modules_flat.append(name)
        name_to_cat[name] = cat

module_to_next_name = {}
for idx, name in enumerate(all_modules_flat):
    if idx < len(all_modules_flat) - 1:
        module_to_next_name[name] = all_modules_flat[idx+1]
    else:
        module_to_next_name[name] = None

# Create pages in reverse order to resolve next_module
created_pages = {}
sections = {cat: [] for cat, _ in structure}

for name in reversed(all_modules_flat):
    module = app_session.modules[name]
    next_name = module_to_next_name[name]
    next_page = created_pages.get(next_name)

    page = st.Page(
        partial(display_module, module, next_module=next_page),
        title=module.title,
        icon="✅" if module.is_solved() else None,
        url_path=name.lower()
    )
    created_pages[name] = page
    sections[name_to_cat[name]].insert(0, page)

# Build navigation
pages = {}

first_module_page = created_pages.get(all_modules_flat[0]) if all_modules_flat else None
pages["Introduction"] = [
    st.Page(partial(display_general, first_module=first_module_page),
            title="Intro", icon="🧐", default=True)
]

for cat, _ in structure:
    if sections[cat]:
        pages[cat] = sections[cat]

pg = st.navigation(pages, position="top", expanded=True)
pg.run()
