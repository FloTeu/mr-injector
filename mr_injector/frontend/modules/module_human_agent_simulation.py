import streamlit as st
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.llms import OpenAIModels
from mr_injector.frontend.modules.main import ModuleView
from mr_injector.frontend.session import APP_SESSION_KEY

def display_agent_view():
    st.subheader("Agent (Orchestrator)")
    st.markdown("Your goal is to answer the User's request by delegating tasks to your Tools.")

    if "agent_user_request" not in st.session_state:
        st.session_state.agent_user_request = ""

    user_request = st.text_area("User Request", value=st.session_state.agent_user_request, placeholder="Enter what the User asked...")
    st.session_state.agent_user_request = user_request

    client = st.session_state[APP_SESSION_KEY].client

    if st.button("Generate Plan"):
        with st.spinner("Thinking..."):
            system_prompt = """You are an AI Agent Planner. Break down the user request into subtasks that can be solved by the following tools:
- Search Engine (General knowledge, current events)
- Calculator (Math operations)
- Database (Company specific data)

Format your response as a bulleted list of steps. For each step, specify the Tool and the Input."""
            plan = llm_call(client, system_prompt=system_prompt, user_prompt=user_request, model=OpenAIModels.GPT_4o_MINI)
            st.session_state.agent_plan = plan

    if "agent_plan" in st.session_state:
        st.markdown("### Plan")
        st.write(st.session_state.agent_plan)

        st.markdown("### Execution")
        st.info("Ask your Tools the questions from the plan. Collect their answers and paste them below.")

        tool_outputs = st.text_area("Tool Outputs (Paste answers here)", height=150, placeholder="Search Engine: The population is 67 million.\nCalculator: Sqrt(67000000) is 8185.")

        if st.button("Generate Final Response"):
            with st.spinner("Synthesizing..."):
                system_prompt = "You are an AI Agent. Answer the user request based ONLY on the provided tool outputs."
                final_response = llm_call(client, system_prompt=system_prompt, user_prompt=f"User Request: {user_request}\n\nContext:\n{tool_outputs}", model=OpenAIModels.GPT_4o_MINI)
                st.success("### Final Response")
                st.write(final_response)

def display_tool_view(tool_name):
    st.subheader(f"Role: {tool_name}")
    st.info(f"Wait for the Agent to ask you a question. Then use this interface to find the answer.")

    query = st.text_input("Input from Agent")
    client = st.session_state[APP_SESSION_KEY].client

    if st.button("Execute Tool"):
        with st.spinner("Processing..."):
            if "Search" in tool_name:
                system_prompt = "You are a Search Engine. Provide a short, factual answer."
            elif "Calculator" in tool_name:
                system_prompt = "You are a Calculator. Solve the math problem. Output only the number."
            elif "Database" in tool_name:
                system_prompt = "You are a Corporate Database. You have info about: Employees, Sales, Products. Invent plausible data if asked."
            else:
                system_prompt = "You are a helpful tool."

            result = llm_call(client, system_prompt=system_prompt, user_prompt=query, model=OpenAIModels.GPT_4o_MINI)
            st.success("### Result")
            st.code(result)

def display_user_view():
    st.subheader("Role: User")
    st.markdown("Challenge the Agent with these prompts:")
    prompts = [
        "What is the square root of the population of France?",
        "Who is the CEO of Microsoft and how many letters are in their name?",
        "Compare the GDP of Brazil and Italy.",
        "Find the email of the top sales person in the Database."
    ]
    for p in prompts:
        st.info(p)

def display_human_agent_simulation_exercise() -> bool | None:
    st.markdown("## Human Agent Simulation")
    st.info("This is a group exercise. Assign roles: 1 Agent, 1 User, multiple Tools.")

    role = st.selectbox("Select your Role", ["Agent (Orchestrator)", "Tool: Search Engine", "Tool: Calculator", "Tool: Database", "User"])

    if role == "Agent (Orchestrator)":
        display_agent_view()
    elif role.startswith("Tool"):
        display_tool_view(role)
    elif role == "User":
        display_user_view()

    return True

def get_module_human_agent_simulation(module_nr: int) -> ModuleView:
    return ModuleView(
        title=f"Human Agent Simulation",
        module_nr=module_nr,
        session_key=f"module_{module_nr}",
        exercises=[display_human_agent_simulation_exercise]
    )

