import os
from pathlib import Path

import streamlit as st
import mr_injector
from openai import OpenAI
from mr_injector.backend.openai import create_open_ai_client
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.modules.module_1_prompt_leaking import get_module_prompt_leaking
from mr_injector.frontend.modules.module_2_prompt_injection import get_module_prompt_injection


def get_open_ai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        api_key = st.text_input("OpenAI key", type="password")
    if api_key:
        return create_open_ai_client(api_key=api_key)
    else:
        return  None


def main():
    col1, col2 = st.columns([0.8, 0.2])
    col1.header("Mr. Injector")
    root_dir = Path(mr_injector.__file__).parent.parent
    col2.image(root_dir / "files/logo_mr_injector.png")
    client = get_open_ai_client()

    my_bar = st.empty()
    modules: list[list[ModuleView]] = []
    if client is not None:
        tabs = st.tabs(["Prompt Leakage", "Prompt Injection"])
        modules.append(get_module_prompt_leaking(client))
        modules.append([get_module_prompt_injection(client)])
        assert len(tabs) == len(modules), "Tabs and modules must have the same length"

        # Display modules
        for module_list, tab in zip(modules,tabs):
            with tab:
                for module in module_list:
                    module.display()
    else:
        st.warning("Pleader provide a openai API key first")

    percentage_solved = 0
    modules_solved: list[str] = []
    for module_list in modules:
        if all(module.is_solved() for module in module_list):
            percentage_solved += (1/len(modules))
            modules_solved.extend([module.title for module in module_list])
        my_bar.progress(percentage_solved, text=f"Modules solved: {', '.join(modules_solved)}")

if __name__ == "__main__":
    main()

