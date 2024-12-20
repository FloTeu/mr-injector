import os
from pathlib import Path

import streamlit as st
import mr_injector
from openai import OpenAI
from mr_injector.backend.openai import create_open_ai_client
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

    if client is not None:
        get_module_prompt_leaking(client).display()
        #get_module_prompt_injection(client).display()
    else:
        st.warning("Pleader provide a openai API key first")


if __name__ == "__main__":
    main()

