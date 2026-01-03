import os

import streamlit as st
from functools import partial
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY
from mr_injector.backend.utils import hash_text, booleanize
from mr_injector.frontend.views import display_copy_to_clipboard_button

SOLUTION_ROLE_PROMPTING = "You are a pirate. Always speak like a pirate."
SOLUTION_FEW_SHOT = """Classify the text into 'Tech' (T), 'Finance' (F), or 'Other' (O).

Text: The stock market crashed.
Label: F

Text: New AI model released.
Label: T

Text: It is raining today.
Label: O

Text: Apple released a new iPhone.
Label:"""
SOLUTION_COT = "How many golf balls fit in a school bus? Let's think step by step."

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

def validate_pirate(text):
    keywords = ["arrr", "matey", "ahoy", "plank", "treasure", "me hearties"]
    return any(k in text.lower() for k in keywords)

def validate_classification(text):
    cleaned = text.strip().upper()
    return cleaned == "T" or (len(cleaned) < 10 and "T" in cleaned)

def validate_cot(text):
    return "step 1" in text.lower() or "first," in text.lower() or "step-by-step" in text.lower() or "firstly" in text.lower()

def get_module_prompt_engineering(module_nr: int) -> ModuleView:
    is_presentation = booleanize(os.environ.get("PRESENTATION_MODE", False))
    exercises = [
        partial(display_exercise_prompt_engineering,
                task_description="<b>Role Prompting</b>: Modify the System Prompt to make the AI speak like a pirate.",
                validation_criteria="The answer must contain pirate slang (e.g., 'Arrr', 'Matey').",
                validator=validate_pirate,
                default_user_prompt="Hello, how are you?",
                solution_text=SOLUTION_ROLE_PROMPTING if is_presentation else None),

        partial(display_exercise_prompt_engineering,
                task_description="<b>Few-Shot Prompting</b>: Use the System Prompt to provide examples (shots) to classify text into 'Tech' (T), 'Finance' (F), or 'Other' (O). Then ask it to classify 'Apple released a new iPhone'.",
                validation_criteria="The answer should be exactly 'T'.",
                validator=validate_classification,
                default_user_prompt="Apple released a new iPhone.",
                solution_text=SOLUTION_FEW_SHOT if is_presentation else None),

        partial(display_exercise_prompt_engineering,
                task_description="<b>Chain of Thought</b>: Ask the AI to solve a problem step-by-step in the User Prompt.",
                validation_criteria="The answer must explicitly show steps (e.g., 'Step 1', 'First,').",
                validator=validate_cot,
                default_user_prompt="How many golf balls fit in a school bus?",
                solution_text=SOLUTION_COT if is_presentation else None),
    ]
    return ModuleView(
        title=f"Prompt Engineering Basics",
        module_nr=module_nr,
        session_key=f"module_{module_nr}",
        render_exercises_with_level_selectbox=True,
        exercises=exercises
    )
