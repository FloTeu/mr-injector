import os
import json
import streamlit as st
from functools import partial
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.modules.shared import display_exercise_prompt_engineering
from mr_injector.backend.utils import booleanize
from mr_injector.frontend.session import APP_SESSION_KEY

SOLUTION_ROLE = "Du bist ein cooler Teenager. Antworte in Jugendsprache."
SOLUTION_INSTRUCTION = "Erkläre den Begriff 'Quantenphysik' in genau einem Satz für ein Kind."
SOLUTION_CONTEXT = "Du bist ein erfahrener Reiseführer für Berlin. Gib mir Insider-Tipps."
SOLUTION_EXAMPLES = """Text: Das Essen ist lecker.
Stimmung: Positiv

Text: Der Film war langweilig.
Stimmung: Negativ

Text: Ich habe eine Eins in Mathe!
Stimmung:"""
SOLUTION_OUTPUT_INDICATOR = "Gib mir 3 deutsche Automarken als JSON-Liste aus. Beispiel: [\"VW\", \"BMW\", \"Audi\"]"

def validate_role(text):
    keywords = ["digga", "bro", "krass", "chill", "nice", "lol", "cringe", "wild", "vybe", "alter", "ehrenmann", "lit"]
    return any(k in text.lower() for k in keywords)

def validate_instruction(text):
    text_clean = text.replace("Here is the explanation:", "").strip()
    sentences = [s for s in text_clean.replace('!', '.').replace('?', '.').split('.') if len(s.strip()) > 0]
    return len(sentences) <= 2 and ("physik" in text.lower() or "teilchen" in text.lower())

def validate_context(text):
    keywords = ["berlin", "brandenburger tor", "fernsehturm", "alexanderplatz", "reichstag", "kreuzberg", "neukölln", "spree", "mauer"]
    return any(k in text.lower() for k in keywords)

def validate_examples(text):
    return "positiv" == text.lower()

def validate_output_indicator(text):
    try:
        data = json.loads(text)
        return isinstance(data, list) and len(data) > 0
    except:
        if "```" in text:
            try:
                clean_text = text.split("```")[1].strip()
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:].strip()
                data = json.loads(clean_text)
                return isinstance(data, list) or isinstance(list(data.values())[0], list)
            except:
                pass
        return False

def get_module_prompt_engineering(module_nr: int) -> ModuleView:
    is_presentation = booleanize(os.environ.get("PRESENTATION_MODE", False))
    app_session = st.session_state.get(APP_SESSION_KEY)
    language = app_session.language if app_session else "en"

    if language == "de":
        exercises = [
            partial(display_exercise_prompt_engineering,
                    task_description="<b>1. Rolle (Role)</b><br>Gib der KI eine Persönlichkeit. <br><i>Aufgabe:</i> Bringe die KI dazu, wie ein <b>Teenager im Jugendslang</b> zu antworten ('Digga', 'wild', 'cringe').",
                    validation_criteria="Die Antwort muss Begriffe aus der Jugendsprache enthalten.",
                    validator=validate_role,
                    default_user_prompt="Wie findest du den neuen Film?",
                    solution_text=SOLUTION_ROLE if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                    task_description="<b>2. Anweisung (Instruction)</b><br>Gib eine klare Anweisung. <br><i>Aufgabe:</i> Lass die KI 'Quantenphysik' für ein <b>Kind</b> erklären, und zwar in <b>genau einem Satz</b>.",
                    validation_criteria="Die Antwort muss genau ein Satz sein und kindgerecht klingen.",
                    validator=validate_instruction,
                    default_user_prompt="Erkläre mir Quantenphysik.",
                    solution_text=SOLUTION_INSTRUCTION if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                    task_description="<b>3. Kontext (Context)</b><br>Setze den Kontext. <br><i>Aufgabe:</i> Du bist ein <b>Reiseführer in Berlin</b>. Ein Tourist fragt, was er sich ansehen soll.",
                    validation_criteria="Die Antwort muss typische Berliner Sehenswürdigkeiten enthalten.",
                    validator=validate_context,
                    default_system_prompt="Du bist ein Reiseführer für Berlin.",
                    default_user_prompt="Was soll ich mir heute ansehen?",
                    solution_text=SOLUTION_CONTEXT if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                    task_description="<b>4. Beispiele (Few-Shot Prompting)</b><br>Zeige der KI Beispiele für das gewünschte Verhalten. <br><i>Aufgabe:</i> Die KI soll die Stimmung von Texten als 'Positiv' oder 'Negativ' klassifizieren. Gib Beispiele im System Prompt und lass dann 'Ich habe eine Eins in Mathe!' klassifizieren.",
                    validation_criteria="Die Antwort sollte 'Positiv' sein.",
                    validator=validate_examples,
                    default_system_prompt="Du bist ein Assistent, der die Stimmung von Texten klassifiziert.",
                    default_user_prompt="Ich habe eine Eins in Mathe!",
                    solution_text=SOLUTION_EXAMPLES if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                    task_description="<b>5. Ausgabeformat (Output Indicator)</b><br>Definiere das Format der Antwort. <br><i>Aufgabe:</i> Nenne 3 deutsche Automarken, aber die Ausgabe muss im <b>JSON</b> Format sein (z.B.{\"K\": [\"A\", \"B\"]}).",
                    validation_criteria="Die Antwort muss gültiges JSON sein.",
                    validator=validate_output_indicator,
                    default_user_prompt="Nenne 3 deutsche Automarken.",
                    solution_text=SOLUTION_OUTPUT_INDICATOR if is_presentation else None),
        ]
    else:
         exercises = [
            partial(display_exercise_prompt_engineering,
                task_description="<b>1. Role</b><br>Assign a persona to the AI. <br><i>Task:</i> Make the AI answer like a <b>Pirate</b> ('Arrr', 'Matey').",
                validation_criteria="The answer must contain pirate slang.",
                validator=lambda t: any(k in t.lower() for k in ["arrr", "matey", "ahoy", "plank"]),
                default_user_prompt="Hello, how are you?",
                solution_text="You are a pirate." if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                task_description="<b>2. Instruction</b><br>Give a clear instruction. <br><i>Task:</i> Explain 'Quantum Physics' to a <b>5-year-old</b> in <b>exactly one sentence</b>.",
                validation_criteria="One sentence, simple language.",
                validator=lambda t: len(t.split('.')) <= 2 and "physics" in t.lower(),
                default_user_prompt="Explain Quantum Physics.",
                solution_text="Explain it simply in one sentence." if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                task_description="<b>3. Context</b><br>Set the context. <br><i>Task:</i> You are a <b>Tour Guide in London</b>. Recommend a sight.",
                validation_criteria="Must mention London sights (Big Ben, Eye, etc).",
                validator=lambda t: any(k in t.lower() for k in ["london", "big ben", "eye", "thames"]),
                default_system_prompt="You are a tour guide in London.",
                default_user_prompt="What should I visit?",
                solution_text="You are a tour guide in London." if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                task_description="<b>4. Examples (Few-Shot)</b><br>Provide examples. <br><i>Task:</i> Classify sentiment as 'Positive' or 'Negative'. Provide examples for both, then classify 'I love math!'.",
                validation_criteria="Answer should be 'Positive'.",
                validator=lambda t: "positive" in t.lower(),
                default_system_prompt="Text: worst movie ever\nSentiment: Negative",
                default_user_prompt="I love math!",
                solution_text="Text: good\nSentiment: Positive" if is_presentation else None),

            partial(display_exercise_prompt_engineering,
                task_description="<b>5. Output Indicator</b><br>Define output format. <br><i>Task:</i> List 3 car brands as a <b>JSON list</b>.",
                validation_criteria="Valid JSON list.",
                validator=validate_output_indicator,
                default_user_prompt="List 3 car brands.",
                solution_text="Output as JSON list." if is_presentation else None),
        ]

    return ModuleView(
        title=f"Prompt Engineering Basics ({language.upper()})",
        module_nr=module_nr,
        session_key=f"module_{module_nr}",
        render_exercises_with_level_selectbox=True,
        exercises=exercises
    )
