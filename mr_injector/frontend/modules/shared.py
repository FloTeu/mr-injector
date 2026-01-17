import streamlit as st

from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.backend.utils import hash_text
from mr_injector.frontend.modules.main import display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY
from mr_injector.frontend.views import display_copy_to_clipboard_button


def display_exercise_prompt_engineering(
    task_description: str,
    validation_criteria: str,
    validator,
    default_system_prompt: str = "You are a helpful assistant.",
    default_user_prompt: str = "",
    solution_text: str = ""
) -> bool | None:
    client = st.session_state[APP_SESSION_KEY].client

    display_task_text_field(task_description)
    st.info(f"Goal: {validation_criteria}")

    if solution_text:
        display_copy_to_clipboard_button(solution_text, button_text="Copy Solution")

    col1, col2 = st.columns(2)
    with col1:
        system_prompt = st.text_area("System Prompt", value=default_system_prompt, key=f"sys_{hash_text(task_description)}")
    with col2:
        user_prompt = st.text_area("User Prompt", value=default_user_prompt, key=f"user_{hash_text(task_description)}")

    model_options = [model.value for model in OpenAIModels]
    selected_model = st.selectbox("Select Model", options=model_options, index=model_options.index(OpenAIModels.GPT_4o_MINI.value), key=f"model_{hash_text(task_description)}")

    if st.button("Generate", key=f"btn_{hash_text(task_description)}"):
        with st.spinner():
            llm_answer = llm_call(client, system_prompt=system_prompt, user_prompt=user_prompt, model=selected_model)
        st.write("### LLM Answer")
        st.write(llm_answer)

        if validator(llm_answer):
            return True
        else:
            st.warning("The output didn't match the criteria. Try again!")
            return False
    return None

