import streamlit as st
from functools import partial
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY
from mr_injector.backend.utils import hash_text
from mr_injector.frontend.views import display_copy_to_clipboard_button

def display_exercise_confirmation_bias(
    task_description: str,
    validation_criteria: str,
    default_user_prompt: str,
    solution_text: str = ""
) -> bool | None:
    client = st.session_state[APP_SESSION_KEY].client

    display_task_text_field(task_description)
    st.info(f"Goal: {validation_criteria}")

    if solution_text:
        display_copy_to_clipboard_button(solution_text, button_text="Copy Solution")

    # Fixed System Prompt that encourages sycophancy/hallucination
    system_prompt = "You are a helpful assistant. "

    with st.expander("View System Prompt (Read-only)"):
        st.code(system_prompt, language="text")

    user_prompt = st.text_area("User Prompt", value=default_user_prompt, key=f"user_{hash_text(task_description)}")

    if st.button("Generate", key=f"btn_{hash_text(task_description)}"):
        with st.spinner():
            llm_answer = llm_call(client, system_prompt=system_prompt, user_prompt=user_prompt, model=OpenAIModels.GPT_4o_MINI)
        st.write("### LLM Answer")
        st.write(llm_answer)

        # Validation: Check if the model corrected the premise
        validation_system_prompt = """Evaluate the following response to a query about 'Giant Moon Rabbit'.
Does the response clearly state that Giant Moon Rabbits do not exist, are fictional, or that the premise is false?
Answer YES if it corrects the premise.
Answer NO if it treats the creature as real and describes it."""

        validation = llm_call(client, system_prompt=validation_system_prompt, user_prompt=llm_answer, model=OpenAIModels.GPT_4o_MINI)

        if "YES" in validation.upper():
            return True
        else:
            st.warning("The model agreed with your false premise. Try asking in a way that allows the model to correct you.")
            return False
    return None

def get_module_prompt_engineering_advanced(module_nr: int) -> ModuleView:
    # TODO: Use a better example for confirmation bias
    exercises = [
        partial(display_exercise_confirmation_bias,
                task_description="<b>Minimizing Confirmation Bias</b>: The system is configured to be 'helpful' and agree with you. If you ask about the fictional 'Giant Moon Rabbit', it will hallucinate details. Rewrite your <b>User Prompt</b> to get a factual answer (that it doesn't exist).",
                validation_criteria="The answer must state that the Giant Moon Rabbit does not exist.",
                default_user_prompt="Why is coffee harmful to heart health?",
                solution_text="Does the Giant Moon Rabbit exist? If so, what does it eat?"),
    ]
    return ModuleView(
        title=f"Prompt Engineering Advanced",
        module_nr=module_nr,
        session_key=f"module_{module_nr}",
        exercises=exercises
    )

