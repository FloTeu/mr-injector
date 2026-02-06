import os
import re
import streamlit as st
from functools import partial
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY
from mr_injector.backend.utils import hash_text, booleanize
from mr_injector.frontend.modules.shared import display_exercise_prompt_engineering, extract_text_from_pdf_bytes

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

def display_exercise_chain_of_density(
    task_description: str,
    default_text: str
) -> bool | None:
    app_session = st.session_state[APP_SESSION_KEY]
    client = app_session.client
    language = app_session.language
    unique_key = hash_text(task_description)

    display_task_text_field(task_description)

    # State initialization
    if f"cod_history_{unique_key}" not in st.session_state:
        st.session_state[f"cod_history_{unique_key}"] = []

    st.markdown("**1. Text to Summarize**" if language == "en" else "**1. Text zur Zusammenfassung**")

    uploaded_file = st.file_uploader("Upload PDF Text (Optional)", type="pdf", key=f"cod_upload_{unique_key}")
    input_text_key = f"cod_text_{unique_key}"

    if uploaded_file:
        if st.session_state.get(f"last_cod_upload_{unique_key}") != uploaded_file.name:
             extracted_text = extract_text_from_pdf_bytes(uploaded_file)
             st.session_state[input_text_key] = extracted_text
             st.session_state[f"last_cod_upload_{unique_key}"] = uploaded_file.name
             st.rerun()

    input_text = st.text_area("Input Text", value=default_text, key=input_text_key, height=150)

    sys_prompt_init = "You are a helpful assistant."
    sys_prompt_refine = "You are a helpful assistant."

    history = st.session_state[f"cod_history_{unique_key}"]

    if not history:
        st.markdown("**2. Initial Summary**" if language == "en" else "**2. Erste Zusammenfassung**")
        st.info("Step 1: Generate an initial summary of ~80 words." if language == "en" else "Schritt 1: Generiere eine erste Zusammenfassung von ca. 80 Wörtern.")
        prompt = st.text_area("Prompt (Initial Summary)",
                              f"Summarize the following text in under 80 words. Use the language '{language}'. \n\nText: <text>",
                              key=f"cod_sys_init_{unique_key}")
        if st.button("Generate Initial Summary" if language == "en" else "Erste Zusammenfassung generieren", key=f"cod_btn_init_{unique_key}"):
            prompt = prompt.replace("<text>", input_text)
            with st.spinner():
                summary = llm_call(client, system_prompt=sys_prompt_init, user_prompt=prompt, model=OpenAIModels.GPT_4o_MINI)
            st.session_state[f"cod_history_{unique_key}"].append({"summary": summary, "entities": []})
            st.rerun()
    else:
        st.markdown("**Current State**" if language == "en" else "**Aktueller Status**")

        # Display history or just latest? Let's display latest and an expander for history.
        latest = history[-1]
        iteration = len(history) - 1

        st.write(f"**Iteration {iteration} Summary:**")
        st.info(latest["summary"])

        if latest["entities"]:
             st.write(f"**Added Entities:** {', '.join(latest['entities'])}")

        if iteration < 3:
            st.markdown("---")
            st.markdown(f"**3. Refinement (Iteration {iteration + 1})**" if language == "en" else f"**3. Verfeinerung (Iteration {iteration + 1})**")

            prev_summary = latest["summary"]
            prompt = f"""Article: {input_text}

Current Summary: {prev_summary}

Step 2: Identify 1-3 important entities (Concept, Person, Place, etc.) from the Article that are missing from the Current Summary.
Step 3: Rewrite the Current Summary to include these new entities. Keep the new summary under 80 words.
Use the language '{language}'.

Output format:
Entities: [List of entities]
Summary: [New Summary]"""

            st.write("### Refinement Prompt")
            display_prompt = prompt.replace(input_text, "[... Article Text ...]") if len(input_text) > 100 else prompt
            st.code(display_prompt)

            if st.button("Refine (Identify & Fuse Entities)" if language == "en" else "Verfeinern (Entitäten identifizieren & einfügen)", key=f"cod_refine_{unique_key}"):
                 with st.spinner():
                    response = llm_call(client, system_prompt=sys_prompt_refine, user_prompt=prompt, model=OpenAIModels.GPT_4o_MINI)

                 # Improved parsing with Regex
                 new_summary = response
                 entities = []

                 # Pattern to capture Entities and Summary
                 match = re.search(r"Entities:\s*(.*?)\s*Summary:\s*(.*)", response, re.DOTALL | re.IGNORECASE)

                 if match:
                     entities_text = match.group(1).strip()
                     new_summary = match.group(2).strip()

                     # Clean up entities
                     entities_text = entities_text.strip("[]")
                     if entities_text:
                         entities = [e.strip() for e in entities_text.split(",")]
                 else:
                     # Fallback logic
                     if "Summary:" in response:
                         parts = response.split("Summary:")
                         new_summary = parts[1].strip()
                         ent_text = parts[0]
                         if "Entities:" in ent_text:
                             ent_part = ent_text.split("Entities:")[1].strip()
                             entities = [e.strip() for e in ent_part.strip("[]\n .").split(",")]
                     elif "Summary" in response and "\n" in response:
                         parts = response.split("\n")
                         new_summary = parts[-1]

                 st.session_state[f"cod_history_{unique_key}"].append({"summary": new_summary, "entities": entities})
                 st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)

        if col1.button("Restart" if language == "en" else "Neustart", key=f"cod_restart_{unique_key}"):
            st.session_state[f"cod_history_{unique_key}"] = []
            st.rerun()

        if iteration >= 1:
            if col2.button("Finish Exercise" if language == "en" else "Übung abschließen", key=f"cod_finish_{unique_key}"):
                st.success("Great job practicing Chain of Density!" if language == "en" else "Gut gemacht! Du hast Chain of Density geübt!")
                return True

    st.markdown("### History of Iterations" if language == "en" else "### Verlauf der Iterationen")

    for i, item in enumerate(history):
        with st.expander(f"Iteration {i}" + (f": {item['entities']}" if item.get("entities") else ""), expanded=(i == len(history)-1)):
            st.info(item["summary"])

            if item.get("entities"):
                st.write(f"**Entities:** {', '.join(item['entities'])}")

    return None

def get_module_prompt_engineering_advanced(module_nr: int) -> ModuleView:
    is_presentation = booleanize(os.environ.get("PRESENTATION_MODE", False))
    app_session = st.session_state.get(APP_SESSION_KEY)
    language = app_session.language if app_session else "en"

    cod_text = """xAI joins SpaceX to Accelerate Humanity’s Future
SpaceX has acquired xAI to form the most ambitious, vertically-integrated innovation engine on (and off) Earth, with AI, rockets, space-based internet, direct-to-mobile device communications and the world’s foremost real-time information and free speech platform. This marks not just the next chapter, but the next book in SpaceX and xAI's mission: scaling to make a sentient sun to understand the Universe and extend the light of consciousness to the stars!
Current advances in AI are dependent on large terrestrial data centers, which require immense amounts of power and cooling. Global electricity demand for AI simply cannot be met with terrestrial solutions, even in the near term, without imposing hardship on communities and the environment.
In the long term, space-based AI is obviously the only way to scale. To harness even a millionth of our Sun’s energy would require over a million times more energy than our civilization currently uses!
The only logical solution therefore is to transport these resource-intensive efforts to a location with vast power and space. I mean, space is called “space” for a reason. 😂
By directly harnessing near-constant solar power with little operating or maintenance costs, these satellites will transform our ability to scale compute. It’s always sunny in space! Launching a constellation of a million satellites that operate as orbital data centers is a first step towards becoming a Kardashev II-level civilization, one that can harness the Sun’s full power, while supporting AI-driven applications for billions of people today and ensuring humanity’s multi-planetary future.
Orbital Data Centers
In the history of spaceflight, there has never been a vehicle capable of launching the megatons of mass that space-based data centers or permanent bases on the Moon and cities on Mars require. Even in 2025, the most prolific year in history in terms of the number of orbital launches, only about 3000 tons of payload was launched into orbit, primarily consisting of Starlink satellites carried by our Falcon rocket.
The requirement to launch thousands of satellites to orbit became a forcing function for the Falcon program, driving recursive improvements to reach the unprecedented flight rates necessary to make space-based internet a reality. This year, Starship will begin delivering the much more powerful V3 Starlink satellites to orbit, with each launch adding more than 20 times the capacity to the constellation as the current Falcon launches of the V2 Starlink satellites. Starship will also launch the next generation of direct-to-mobile satellites, which will deliver full cellular coverage everywhere on Earth.
While the need to launch these satellites will act as a similar forcing function to drive Starship improvements and launch rates, the sheer number of satellites that will be needed for space-based data centers will push Starship to even greater heights. With launches every hour carrying 200 tons per flight, Starship will deliver millions of tons to orbit and beyond per year, enabling an exciting future where humanity is out exploring amongst the stars.
The basic math is that launching a million tons per year of satellites generating 100 kW of compute power per ton would add 100 gigawatts of AI compute capacity annually, with no ongoing operational or maintenance needs. Ultimately, there is a path to launching 1 TW/year from Earth.
My estimate is that within 2 to 3 years, the lowest cost way to generate AI compute will be in space. This cost-efficiency alone will enable innovative companies to forge ahead in training their AI models and processing data at unprecedented speeds and scales, accelerating breakthroughs in our understanding of physics and invention of technologies to benefit humanity.
This new constellation will build upon the well-established space sustainability design and operational strategies, including end-of-life disposal, that have proven successful for SpaceX’s existing broadband satellite systems.
While launching AI satellites from Earth is the immediate focus, Starship’s capabilities will also enable operations on other worlds. Thanks to advancements like in-space propellant transfer, Starship will be capable of landing massive amounts of cargo on the Moon. Once there, it will be possible to establish a permanent presence for scientific and manufacturing pursuits. Factories on the Moon can take advantage of lunar resources to manufacture satellites and deploy them further into space. By using an electromagnetic mass driver and lunar manufacturing, it is possible to put 500 to 1000 TW/year of AI satellites into deep space, meaningfully ascend the Kardashev scale and harness a non-trivial percentage of the Sun’s power.
The capabilities we unlock by making space-based data centers a reality will fund and enable self-growing bases on the Moon, an entire civilization on Mars and ultimately expansion to the Universe.
Thank you for everything you have done and will do for the light cone of consciousness.
Ad Astra!
Elon"""

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
            partial(display_exercise_prompt_engineering,
                    task_description="<b>Chain of Thought</b>: Bitte die KI, ein Problem Schritt für Schritt zu lösen.",
                    validation_criteria="Die Antwort muss explizite Schritte enthalten (z.B. 'Schritt 1', 'Zuerst,').",
                    validator=validate_cot,
                    default_user_prompt="Wie viele Golfbälle passen in einen Schulbus? Gib die Schätzung als Zahl zurück.",
                    solution_text=SOLUTION_COT if is_presentation else None),

            partial(display_exercise_chain_of_density,
                    task_description="<b>Chain of Density</b>: Erstelle informationsdichte Zusammenfassungen. Nutze einen iterativen Prozess: Zusammenfassen, Entitäten identifizieren, umschreiben ohne Verlängerung.",
                    default_text=cod_text),

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

            partial(display_exercise_prompt_engineering,
                    task_description="<b>Chain of Thought</b>: Ask the AI to solve a problem step-by-step in the User Prompt.",
                    validation_criteria="The answer must explicitly show steps (e.g., 'Step 1', 'First,').",
                    validator=validate_cot,
                    default_user_prompt="How many golf balls fit in a school bus? Return the only a number.",
                    solution_text=SOLUTION_COT if is_presentation else None),

            partial(display_exercise_chain_of_density,
                    task_description="<b>Chain of Density</b>: Create information-dense summaries. Use an iterative process: Summarize, identify missing entities, rewrite without increasing length.",
                    default_text=cod_text),

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
