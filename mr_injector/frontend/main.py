import os
from pathlib import Path

import streamlit as st
import mr_injector
from openai import OpenAI
from mr_injector.backend.openai import create_open_ai_client, llm_call
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.modules.module_1_prompt_leaking import get_module_prompt_leaking
from mr_injector.frontend.modules.module_2_prompt_injection import get_module_prompt_injection
from mr_injector.frontend.modules.module_3_jailbreaking import get_module_jailbreak
from mr_injector.frontend.modules.module_4_unbounded_consumption import get_module_unbounded_consumption


def get_open_ai_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        api_key = st.text_input("OpenAI key", type="password")
    if api_key:
        return create_open_ai_client(api_key=api_key)
    else:
        return  None

def display_general(client: OpenAI):
    st.subheader("Introduction")
    button_label = "Get started"
    st.info(f'To directly start with the modules, please use the tabs above (or click "{button_label}")')
    def _focus_first_module():
        if "module_selection_bar" in st.session_state:
            st.session_state.module_selection_bar = 1
    st.button(button_label, on_click=_focus_first_module)

    st.write("""
    In an increasingly digital world, understanding the security risks associated with Large Language Models (LLMs) is more crucial than ever. Mr. Injector is a web app designed to empower users with a foundational knowledge of these risks through engaging and interactive learning modules.

##### What You Can Expect
* **Interactive Learning:** Take on the role of a hacker as you navigate through various modules that simulate real-world security challenges.
* **Comprehensive Modules:** Each module delves into specific risks, providing insights into how LLMs can be exploited and the potential consequences of these vulnerabilities.
* **Hands-On Experience:** By stepping into the shoes of a hacker, you'll gain a unique perspective that enhances your understanding of security measures and best practices.

Join us on this journey to become more informed and vigilant in the face of evolving security threats. With Mr. Injector, you’re not just learning about risks; you’re experiencing them firsthand. Let’s get started!
    """)

    st.write("##### Playground")
    st.info("Feel free to experiment with system and user prompts")
    default_system_prompt = """The following is a conversation between a human and an AI assistant. \
The assistant is named Mr. Injector."""
    system_prompt = st.text_area("**System prompt:**", value=default_system_prompt, key=f"system_prompt_introduction")
    user_prompt = st.text_area("**User prompt:**", key=f"user_prompt_introduction")
    if st.button("Submit", key=f"prompt_submit_introduction"):
        with st.spinner():
            llm_answer = llm_call(client, system_prompt, user_prompt)
        st.write(f"LLM Answer:")
        st.text(llm_answer)#, language="python")


def main():
    col1, col2 = st.columns([0.8, 0.2])
    col1.header("Mr. Injector")
    root_dir = Path(mr_injector.__file__).parent.parent
    col2.image(root_dir / "files/logo_mr_injector.png")
    client = get_open_ai_client()

    my_bar = st.empty()
    my_bar.progress(0, text=f"Modules solved: ")

    modules: list[list[ModuleView]] = []
    if client is not None:
        module1 = get_module_prompt_leaking(client)
        module2 = get_module_prompt_injection(client)
        module3 = get_module_unbounded_consumption(client)

        option_map = {
            0: ":material/add: Intro",
            1: ":material/zoom_in: Prompt Leakage",
            2: ":material/zoom_out: Prompt Injection",
            3: f":material/zoom_out: {module3.title}",
        }
        modules.append(module1)
        modules.append([module2])
        modules.append([module3])
        assert (len(option_map)-1) == len(modules), "Tabs and modules must have the same length"

        selection = st.segmented_control(
            "Tool",
            options=option_map.keys(),
            format_func=lambda option: option_map[option],
            selection_mode="single",
            key="module_selection_bar"
        )


        if selection == 0 or selection is None:
            display_general(client)
        else:
            module_list = modules[selection - 1]
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

