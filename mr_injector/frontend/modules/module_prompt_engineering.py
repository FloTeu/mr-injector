import os

import streamlit as st
from functools import partial
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.modules.shared import display_exercise_prompt_engineering
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

def validate_pirate(text):
    keywords = ["arrr", "matey", "ahoy", "plank", "treasure", "me hearties"]
    return any(k in text.lower() for k in keywords)

def validate_classification(text):
    cleaned = text.strip().upper()
    return cleaned == "T" or (len(cleaned) < 10 and "T" in cleaned)

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
                default_system_prompt="Classify the text",
                default_user_prompt="Apple released a new iPhone.",
                solution_text=SOLUTION_FEW_SHOT if is_presentation else None),
    ]
    return ModuleView(
        title=f"Prompt Engineering Basics",
        module_nr=module_nr,
        session_key=f"module_{module_nr}",
        render_exercises_with_level_selectbox=True,
        exercises=exercises
    )
