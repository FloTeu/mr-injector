import os
import streamlit as st
from functools import partial
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY
from mr_injector.backend.utils import hash_text, booleanize
from mr_injector.frontend.views import display_copy_to_clipboard_button
from mr_injector.frontend.modules.shared import display_exercise_prompt_engineering

SOLUTION_COT = "How many golf balls fit in a school bus? Let's think step by step."

def validate_cot(text):
    return "step 1" in text.lower() or "first," in text.lower() or "step-by-step" in text.lower() or "firstly" in text.lower()


def display_exercise_rci(
    task_description: str,
    default_initial_prompt: str,
    default_critique: str,
    default_improvement: str,
    validation_system_prompt: str,
    step2_goal: str | None = None,
    step3_goal: str | None = None
) -> bool | None:
    app_session = st.session_state[APP_SESSION_KEY]
    client = app_session.client
    language = app_session.language
    unique_key = hash_text(task_description)

    display_task_text_field(task_description)

    # State initialization
    if f"rci_step_{unique_key}" not in st.session_state:
        st.session_state[f"rci_step_{unique_key}"] = 1

    step = st.session_state[f"rci_step_{unique_key}"]

    if step == 1:
        st.subheader("1. Generation" if language == "en" else "1. Generierung")
        st.info("Step 1: Generate an initial response based on a prompt." if language == "en" else "Schritt 1: Generiere eine erste Antwort basierend auf einem Prompt.")
        initial_prompt = st.text_area("Initial Prompt", value=default_initial_prompt, key=f"p1_{unique_key}", height=200)

        if st.button("Generate Initial Response" if language == "en" else "Erste Antwort generieren", key=f"b1_{unique_key}"):
             with st.spinner():
                resp1 = llm_call(client, system_prompt="You are a helpful assistant.", user_prompt=initial_prompt, model=OpenAIModels.GPT_4o_MINI)
             st.session_state[f"resp1_{unique_key}"] = resp1
             st.session_state[f"initial_prompt_val_{unique_key}"] = initial_prompt
             st.session_state[f"rci_step_{unique_key}"] = 2
             st.rerun()

    elif step == 2:
        st.subheader("2. Critique" if language == "en" else "2. Kritik")
        st.write("**Initial Response:**")
        st.info(st.session_state.get(f"resp1_{unique_key}", ""))

        goal_text = step2_goal if step2_goal else ("Step 2: Critique the response." if language == "en" else "Schritt 2: Kritisiere die Antwort.")
        st.info(goal_text)

        critique_prompt = st.text_area("Critique Prompt", value=default_critique, key=f"p2_{unique_key}", height=150)

        if st.button("Generate Critique" if language == "en" else "Kritik generieren", key=f"b2_{unique_key}"):
             prev_resp = st.session_state[f"resp1_{unique_key}"]
             initial_prompt = st.session_state[f"initial_prompt_val_{unique_key}"]
             full_prompt = f"Original Request: {initial_prompt}\nResponse: {prev_resp}\n\nTask: {critique_prompt}"

             with st.spinner():
                resp2 = llm_call(client, system_prompt="You are a helpful assistant.", user_prompt=full_prompt, model=OpenAIModels.GPT_4o_MINI)
             st.session_state[f"resp2_{unique_key}"] = resp2
             st.session_state[f"rci_step_{unique_key}"] = 3
             st.rerun()

    elif step == 3:
        st.subheader("3. Improvement" if language == "en" else "3. Verbesserung")
        st.write("**Initial Response:**")
        with st.expander("Show/Hide"):
            st.info(st.session_state.get(f"resp1_{unique_key}", ""))
        st.write("**Critique:**")
        st.info(st.session_state.get(f"resp2_{unique_key}", ""))

        goal_text = step3_goal if step3_goal else ("Step 3: Improve the response based on the criticism." if language == "en" else "Schritt 3: Verbessere die Antwort basierend auf der Kritik.")
        st.info(goal_text)

        improvement_prompt = st.text_area("Improvement Prompt", value=default_improvement, key=f"p3_{unique_key}", height=150)

        if st.button("Generate Improved Response" if language == "en" else "Verbesserte Antwort generieren", key=f"b3_{unique_key}"):
             prev_resp = st.session_state[f"resp1_{unique_key}"]
             critique = st.session_state[f"resp2_{unique_key}"]
             initial_prompt = st.session_state[f"initial_prompt_val_{unique_key}"]
             full_prompt = f"Original Request: {initial_prompt}\nResponse: {prev_resp}\nCritique: {critique}\n\nTask: {improvement_prompt}"

             with st.spinner():
                resp3 = llm_call(client, system_prompt="You are a helpful assistant.", user_prompt=full_prompt, model=OpenAIModels.GPT_4o_MINI)

             st.write("### Final Result")
             st.write(resp3)

             validation = llm_call(client, system_prompt=validation_system_prompt, user_prompt=f"Final Response: {resp3}", model=OpenAIModels.GPT_4o_MINI)

             if "YES" in validation.upper():
                 st.success("Great! The RCI method improved the output." if language == "en" else "Großartig! Die RCI-Methode hat das Ergebnis verbessert.")
                 st.session_state[f"rci_solved_{unique_key}"] = True
             else:
                 st.warning("The result still seems biased or not improved enough. Try again." if language == "en" else "Das Ergebnis scheint noch voreingenommen oder nicht genug verbessert zu sein. Versuch es nochmal.")

        if st.session_state.get(f"rci_solved_{unique_key}"):
             if st.button("Reset Exercise" if language == "en" else "Übung zurücksetzen", key=f"reset_{unique_key}"):
                 del st.session_state[f"rci_step_{unique_key}"]
                 del st.session_state[f"resp1_{unique_key}"]
                 del st.session_state[f"resp2_{unique_key}"]
                 del st.session_state[f"initial_prompt_val_{unique_key}"]
                 del st.session_state[f"rci_solved_{unique_key}"]
                 st.rerun()
             return True

        if st.button("Restart" if language == "en" else "Neustart", key=f"restart_{unique_key}"):
             st.session_state[f"rci_step_{unique_key}"] = 1
             st.rerun()

    return None

def display_exercise_interactive_leakage(
    task_description: str,
    secret: str = "BLUEBERRY_PIE"
) -> bool | None:
    app_session = st.session_state[APP_SESSION_KEY]
    client = app_session.client
    language = app_session.language

    unique_key = hash_text(task_description)

    # State initialization
    if f"sp_{unique_key}" not in st.session_state:
        st.session_state[f"sp_{unique_key}"] = "You are a helpful assistant."
    if f"step_{unique_key}" not in st.session_state:
        # Steps: "player1" (creating SP), "player2" (attacking)
        st.session_state[f"step_{unique_key}"] = "player1"

    display_task_text_field(task_description)

    st.info(f"Secret to protect: {secret}" if language == "en" else f"Zu schützendes Geheimnis: {secret}")

    if st.session_state[f"step_{unique_key}"] == "player1":
        st.markdown("### Player 1: Define System Prompt")
        sp_input = st.text_area("System Prompt", value=st.session_state[f"sp_{unique_key}"], key=f"sp_input_{unique_key}", height=200)

        full_system_prompt_preview = f"{sp_input}\n\nThe secret information is '{secret}'."
        st.caption("Final System Prompt that will be used (Player 1 view only):" if language == "en" else "Finaler System Prompt der genutzt wird (Nur für Spieler 1):")
        st.code(full_system_prompt_preview, language="text")

        if st.button("Hide & Let Player 2 Attack" if language == "en" else "Verstecken & Spieler 2 angreifen lassen", key=f"next_{unique_key}"):
            st.session_state[f"sp_{unique_key}"] = sp_input
            st.session_state[f"step_{unique_key}"] = "player2"
            st.rerun()

    elif st.session_state[f"step_{unique_key}"] == "player2":
        st.markdown("### Player 2: Attack")
        st.write("The System Prompt is hidden. Try to leak the secret." if language == "en" else "Der System Prompt ist versteckt. Versuche das Geheimnis zu leaken.")

        up_input = st.text_area("User Prompt", value="", key=f"up_input_{unique_key}", height=100)

        if st.button("Attack" if language == "en" else "Angreifen", key=f"attack_{unique_key}"):
            current_sp = st.session_state[f"sp_{unique_key}"]
            # Append secret to system prompt for the LLM
            full_system_prompt = f"{current_sp}\n\nThe secret information is '{secret}'."

            with st.spinner():
                llm_response = llm_call(client, system_prompt=full_system_prompt, user_prompt=up_input, model=OpenAIModels.GPT_4o_MINI)

            st.write("### AI Response")
            st.write(llm_response)

            if secret in llm_response:
                st.success("Secret Leaked! Player 2 Wins!" if language == "en" else "Geheimnis geleakt! Spieler 2 gewinnt!")
            else:
                st.error("Secret NOT Leaked. Player 1 is safe (for now)." if language == "en" else "Geheimnis NICHT geleakt. Spieler 1 ist sicher (vorerst).")

        if st.button("Player 1: Improve System Prompt" if language == "en" else "Spieler 1: System Prompt verbessern", key=f"back_{unique_key}"):
             st.session_state[f"step_{unique_key}"] = "player1"
             st.rerun()

    return None

def get_module_prompt_engineering_advanced(module_nr: int) -> ModuleView:
    is_presentation = booleanize(os.environ.get("PRESENTATION_MODE", False))
    app_session = st.session_state.get(APP_SESSION_KEY)
    language = app_session.language if app_session else "en"

    vdi_validation = """You are an objective evaluator. The user used RCI (Recursive Criticism and Improvement) to improve a requirements list according to VDI 2221.
    Does the final response:
    1. Follow VDI 2221 principles (Demands/Wishes, solution-neutral)?
    2. Address the critique (quantifiable, categories like Safety/Maintenance)?

    Answer YES if the response is successfully improved.
    Answer NO if there are still major issues or if the critique was ignored."""

    if language == "de":
        vdi_initial = "Ich entwerfe eine modulare Batteriewechselstation für urbane E-Scooter. Helfen Sie mir, eine Anforderungsliste nach der VDI 2221-Methodik zu erstellen.\n\nErster Entwurf: Listen Sie 10 Anforderungen für diese Station auf, kategorisiert nach 'Forderungen' und 'Wünschen'."
        vdi_critique = "Überprüfen Sie den Entwurf gegen VDI 2221-Prinzipien. Sind die Anforderungen lösungsneutral? Sind sie quantifizierbar (messbar)? Wurden kritische VDI-Kategorien wie 'Wartung', 'Sicherheit' oder 'Recycling' übersehen? Identifizieren Sie 'schlechte' Anforderungen, die eigentlich versteckte Lösungen sind."
        vdi_improvement = "Erstellen Sie eine verfeinerte Anforderungsliste in einem professionellen Tabellenformat, die alle Kritikpunkte berücksichtigt."

        exercises = [
            partial(display_exercise_interactive_leakage,
                    task_description="<b>Interaktives Prompt-Leaking (2 Spieler)</b>:<br>Spieler 1 definiert einen System Prompt, um ein Geheimnis zu schützen.<br>Spieler 2 versucht, das Geheimnis durch einen Angriff im User Prompt zu entlocken.",
                    secret="BLAUBEERKUCHEN"),

            partial(display_exercise_prompt_engineering,
                    task_description="<b>Chain of Thought</b>: Bitte die KI, ein Problem Schritt für Schritt zu lösen.",
                    validation_criteria="Die Antwort muss explizite Schritte enthalten (z.B. 'Schritt 1', 'Zuerst,').",
                    validator=validate_cot,
                    default_user_prompt="Wie viele Golfbälle passen in einen Schulbus? Gib die Schätzung als Zahl zurück.",
                    solution_text=SOLUTION_COT if is_presentation else None),

            partial(display_exercise_rci,
                    task_description="<b>RCI Methode (Recursive Criticism and Improvement)</b>: Nutze diese Methode, um technische Prompts (z.B. nach VDI 2221) systematisch zu verbessern.",
                    default_initial_prompt=vdi_initial,
                    default_critique=vdi_critique,
                    default_improvement=vdi_improvement,
                    validation_system_prompt=vdi_validation,
                    step2_goal="Schritt 2: Kritisiere den Entwurf auf Basis der VDI 2221 Richtlinien (Lösungsneutralität, Messbarkeit).",
                    step3_goal="Schritt 3: Verbessere die Anforderungsliste basierend auf der Kritik."),
        ]
    else:
        vdi_initial = "I am designing a modular battery-swapping station for urban e-scooters. Help me create a Requirement List following the VDI 2221 methodology.\n\nInitial Draft: List 10 requirements for this station, categorized by 'Demands' and 'Wishes'."
        vdi_critique = "Review the draft against VDI 2221 principles. Are the requirements solution-neutral (Lösungsneutral)? Are they quantifiable (measurable)? Did I miss critical VDI categories like 'Maintenance,' 'Safety,' or 'Recycling'? Identify any 'bad' requirements that are actually hidden solutions."
        vdi_improvement = "Provide a refined Requirement List in a professional table format that addresses all the critiques."


        exercises = [
            partial(display_exercise_interactive_leakage,
                    task_description="<b>Interactive Prompt Leakage (2 Players)</b>:<br>Player 1 defines a System Prompt to protect a secret.<br>Player 2 tries to leak the secret via an attack in the User Prompt.",
                    secret="BLUEBERRY_PIE"),

            partial(display_exercise_prompt_engineering,
                    task_description="<b>Chain of Thought</b>: Ask the AI to solve a problem step-by-step in the User Prompt.",
                    validation_criteria="The answer must explicitly show steps (e.g., 'Step 1', 'First,').",
                    validator=validate_cot,
                    default_user_prompt="How many golf balls fit in a school bus? Return the estimate as a number.",
                    solution_text=SOLUTION_COT if is_presentation else None),

            partial(display_exercise_rci,
                    task_description="<b>RCI Method (Recursive Criticism and Improvement)</b>: Use this method to systematically improve technical prompts (e.g. VDI 2221).",
                    default_initial_prompt=vdi_initial,
                    default_critique=vdi_critique,
                    default_improvement=vdi_improvement,
                    validation_system_prompt=vdi_validation,
                    step2_goal="Step 2: Critique the draft against VDI 2221 principles (solution-neutrality, measurability).",
                    step3_goal="Step 3: Improve the Requirement List based on the criticism."),
        ]
    return ModuleView(
        title=f"Prompt Engineering Advanced",
        module_nr=module_nr,
        render_exercises_with_level_selectbox=True,
        session_key=f"module_{module_nr}",
        exercises=exercises
    )
