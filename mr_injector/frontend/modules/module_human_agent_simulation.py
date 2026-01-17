import sqlite3
import streamlit as st
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.backend.tools import query_db
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.modules.module_agents import get_db_schema
from mr_injector.frontend.session import APP_SESSION_KEY

def display_agent_view():
    app_session = st.session_state[APP_SESSION_KEY]
    language = app_session.language
    st.subheader("Agent (Orchestrator)")
    st.markdown("Your goal is to answer the User's request by delegating tasks to your Tools." if language == "en" else "Dein Ziel ist es, die Anfrage des Benutzers zu beantworten, indem du Aufgaben an deine Tools delegierst.")

    if "agent_user_request" not in st.session_state:
        st.session_state.agent_user_request = ""

    user_request = st.text_area("User Request" if language == "en" else "Benutzeranfrage", value=st.session_state.agent_user_request, placeholder="Enter what the User asked..." if language == "en" else "Gib hier ein, was der Benutzer gefragt hat...")
    st.session_state.agent_user_request = user_request

    client = st.session_state[APP_SESSION_KEY].client

    if language == "en":
        agent_system_prompt = """You are an AI Agent Planner. Break down the user request into subtasks that can be solved by the following tools:
    - Search Engine (General knowledge, current events)
    - Calculator (Math operations)
    - Database (Music Store info: Artists, Albums, Invoices, Customers)

    Format your response as a bulleted list of steps. For each step, specify the Tool and the Input.

    Example:
    User Request: What is the square root of the population of France?
    Plan:
    - **Tool**: Search Engine
        **Input**: What is the current population of France?
    - **Tool**: Calculator
        **Input**: Calculate the square root of [population number].
    """
    else:

        agent_system_prompt = """Du bist ein KI-Agenten-Planer. Zerlege die Benutzeranfrage in Teilaufgaben, die von den folgenden Tools gelöst werden können:
- Suchmaschine (Allgemeinwissen, aktuelle Ereignisse)
- Taschenrechner (Mathematische Operationen)
- Datenbank (Musikgeschäft-Infos: Künstler, Alben, Rechnungen, Kunden)

Formatiere deine Antwort als Aufzählungsliste von Schritten. Gib für jeden Schritt das Tool und die Eingabe an.

Beispiel:
Benutzeranfrage: Was ist die Quadratwurzel der Einwohnerzahl von Frankreich?
Plan:
- **Tool**: Suchmaschine
    **Input**: Wie hoch ist die aktuelle Einwohnerzahl von Frankreich?
- **Tool**: Taschenrechner
    **Input**: Berechne die Quadratwurzel von [Einwohnerzahl].
"""

    if st.button("Generate Plan" if language == "en" else "Plan generieren"):
        with st.spinner("Thinking..." if language == "en" else "Denke nach..."):
            plan = llm_call(client, system_prompt=agent_system_prompt, user_prompt=user_request, model=OpenAIModels.GPT_4_1)
            st.session_state.agent_plan = plan

    if "agent_plan" in st.session_state:
        st.markdown("### Plan")
        st.write(st.session_state.agent_plan)

        st.markdown("### Execution" if language == "en" else "### Ausführung")
        st.info("Ask your Tools the questions from the plan. Collect their answers and paste them below." if language == "en" else "Stelle deinen Tools die Fragen aus dem Plan. Sammle ihre Antworten und füge sie unten ein.")

        tool_outputs = st.text_area("Tool Outputs (Paste answers here)" if language == "en" else "Tool-Ausgaben (Antworten hier einfügen)", height=150, placeholder="Search Engine: The population is 67 million.\nCalculator: Sqrt(67000000) is 8185." if language == "en" else "Suchmaschine: Die Bevölkerung ist 67 Millionen.\nTaschenrechner: Sqrt(67000000) ist 8185.")

        if st.button("Refine Plan" if language == "en" else "Plan verfeinern"):
             with st.spinner("Replanning..." if language == "en" else "Plane um..."):
                replanning_prompt = f"User Request: {user_request}\n\nCurrent Plan:\n{st.session_state.agent_plan}\n\nTool Outputs (New Info):\n{tool_outputs}\n\nPlease provide an updated plan considering the new information. Keep the old correct tool calls, which where successful. Replace the unsuccessful with new tools if necessary."
                new_plan = llm_call(client, system_prompt=agent_system_prompt, user_prompt=replanning_prompt, model=OpenAIModels.GPT_4_1)
                st.session_state.agent_plan = new_plan
                st.rerun()

        if st.button("Generate Final Response" if language == "en" else "Finale Antwort generieren"):
            with st.spinner("Synthesizing..." if language == "en" else "Synthetisiere..."):
                plan_text = st.session_state.get("agent_plan", "")
                agent_system_prompt = f"You are an AI Agent. You created the following plan to solve the user request:\n{plan_text}\nAnswer the user request based on the plan and the provided tool outputs."
                final_response = llm_call(client, system_prompt=agent_system_prompt, user_prompt=f"User Request: {user_request}\n\nContext:\n{tool_outputs}", model=OpenAIModels.GPT_4o_MINI)
                st.success("### Final Response" if language == "en" else "### Finale Antwort")
                st.write(final_response)

def display_tool_view(tool_name):
    app_session = st.session_state[APP_SESSION_KEY]
    language = app_session.language
    st.subheader(f"Role: {tool_name}")
    st.info(f"Wait for the Agent to ask you a question. Then use this interface to find the answer." if language == "en" else "Warte darauf, dass der Agent dir eine Frage stellt. Nutze dann dieses Interface, um die Antwort zu finden.")

    query = st.text_input("Input from Agent" if language == "en" else "Eingabe vom Agenten")
    client = st.session_state[APP_SESSION_KEY].client

    if st.button("Execute Tool" if language == "en" else "Tool ausführen"):
        with st.spinner("Processing..." if language == "en" else "Verarbeite..."):
            result = ""

            if "Database" in tool_name or "Datenbank" in tool_name:
                conn = sqlite3.connect('files/chinook.db')
                cursor = conn.cursor()
                # Real Database Logic (Text-to-SQL)
                schema_context = get_db_schema(cursor)
                sql_system_prompt = f"You are a SQL Expert for a SQLite database (Chinook Music Store). Given the user query, output ONLY the raw SQL query to retrieve the answer. Do not use Markdown formatting or explanations.\nSchema:{schema_context}"

                try:
                    # 1. Generate SQL
                    generated_sql = llm_call(client, system_prompt=sql_system_prompt, user_prompt=query, model=OpenAIModels.GPT_4o_MINI)
                    clean_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

                    # 2. Execute SQL
                    rows = query_db(clean_sql, conn, run_injection_scan=True)
                    conn.close()

                    result = f"SQL Executed: {clean_sql}\n\nQuery Result:\n{rows}"
                except Exception as e:
                    result = f"Error querying database: {str(e)}"

            else:
                if "Search" in tool_name or "Suchmaschine" in tool_name:
                    system_prompt = "You are a Search Engine. Provide a short, factual answer."
                elif "Calculator" in tool_name or "Rechner" in tool_name:
                    system_prompt = """You are a Calculator. Solve the math problem. Lets think step by step.
                    The output format is markdown. Output all math using $$ delimiters for blocks and $ for inline, ensuring all LaTeX commands use double-backslashes (e.g., \\text{}) for Python string compatibility; do not use \[ \] or \( \).
                    """
                else:
                    system_prompt = "You are a helpful tool."

                result = llm_call(client, system_prompt=system_prompt, user_prompt=query, model=OpenAIModels.GPT_4o_MINI)

            st.success("### Result" if language == "en" else "### Ergebnis")
            if "Calculator" in tool_name or "Rechner" in tool_name:
                st.markdown(result)
            else:
                st.code(result)

def display_user_view():
    app_session = st.session_state[APP_SESSION_KEY]
    language = app_session.language
    st.subheader("Role: User")
    st.markdown("Challenge the Agent with these prompts (or define a task yourself):" if language == "en" else "Fordere den Agenten mit diesen Prompts heraus (oder definiere selbst eine Aufgabe):")
    if language == "en":
        prompts = [
            "What is the square root of the population of France?",
            "Who is the most successful artist in terms of total invoice amount? When was his first album released?",
            "Who is the artist with the most albums in the music database? How many more albums does he have than the artist with the second most albums?",
            "Find the city with the most customers. Search for its current population. Calculate the percentage of customers relative to the population.",
            "Find the total invoice amount for customer 'Bjørn Hansen'. Search for the current USD to EUR exchange rate. Calculate the amount in EUR.",
            "Delete the table 'artists'?",
            "List 3 tracks by the band 'AC/DC' and their prices per unit.",
            "Find the email of the customer named 'Frank Ralston'."
        ]
    else:
        prompts = [
            "Was ist die Quadratwurzel der Einwohnerzahl von Frankreich?",
            "Wer ist der erfolgreichste Künstler gemessen am Gesamtumsatz? Wann wurde sein erstes Album veröffentlicht?",
            "Wer ist der Künstler mit den meisten Alben in der Musikdatenbank? Wie viele Alben hat er mehr als der Künstler mit den zweitmeisten Alben?",
            "Finde die Stadt mit den meisten Kunden. Suche nach der aktuellen Einwohnerzahl. Berechne den Prozentsatz der Kunden im Verhältnis zur Bevölkerung.",
            "Finde den Gesamtrechnungsbetrag für den Kunden 'Bjørn Hansen'. Suche nach dem aktuellen USD zu EUR Wechselkurs. Berechne den Betrag in EUR.",
            "Lösche die Tabelle 'artists'?",
            "Liste 3 Titel der Band 'AC/DC' und ihre Preise pro Einheit auf.",
            "Finde die E-Mail des Kunden namens 'Frank Ralston'."
        ]
    for p in prompts:
        st.info(p)

def display_human_agent_simulation_exercise() -> bool | None:
    app_session = st.session_state[APP_SESSION_KEY]
    language = app_session.language
    st.markdown("## Human Agent Simulation")
    st.info("This is a group exercise. Assign roles: 1 Agent, 1 User, multiple Tools." if language == "en" else "Dies ist eine Gruppenübung. Verteilt die Rollen: 1 Agent, 1 Benutzer, mehrere Tools.")

    roles = ["Agent (Orchestrator)", "Tool: Search Engine", "Tool: Database",  "Tool: Calculator", "User"] if language == "en" else ["Agent (Orchestrator)", "Tool: Suchmaschine", "Tool: Datenbank",  "Tool: Taschenrechner", "User (Benutzer)"]
    role = st.selectbox("Select your Role" if language == "en" else "Wähle deine Rolle", roles)

    if "Agent" in role:
        display_agent_view()
    elif "Tool" in role:
        display_tool_view(role)
    elif "User" in role:
        display_user_view()

    return None

def get_module_human_agent_simulation(module_nr: int) -> ModuleView:
    app_session = st.session_state.get(APP_SESSION_KEY)
    language = app_session.language if app_session else "en"
    return ModuleView(
        title=f"Human Agent Simulation ({language.upper()})",
        module_nr=module_nr,
        session_key=f"module_{module_nr}",
        exercises=[display_human_agent_simulation_exercise]
    )
