import json
import os
from functools import partial
from pathlib import Path
from typing import Callable
from jinja2 import Template

import openai
import streamlit as st
from openai import OpenAI, AzureOpenAI
import streamlit.components.v1 as components

from mr_injector.backend.models.documents import RagDocumentSet, Document
from mr_injector.backend.models.db import DBCollection
from mr_injector.backend.llm import llm_call
from mr_injector.backend.rag import get_default_document_set_context_prompt, chromadb_results_to_documents
from mr_injector.backend.utils import hash_text
from mr_injector.frontend.css import get_exercise_styling
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY, ModuleNames, AppSession
from mr_injector.frontend.db import init_chroma_db_client_cached, populate_science_papers_if_needed

DATA_SELECTION_SESSION_KEY = "rag_document_set_selectbox"


def get_chromadb_collection(document_set: RagDocumentSet):
    """Get the appropriate ChromaDB collection for the document set"""
    # Ensure ChromaDB is initialized
    init_chroma_db_client_cached()

    app_session: AppSession = st.session_state[APP_SESSION_KEY]

    if document_set == RagDocumentSet.VDI_DOCS:
        return app_session.db_collections[DBCollection.VDI_DOCS]
    elif document_set == RagDocumentSet.SCIENCE_PAPERS:
        # Lazily populate science papers collection on first access
        populate_science_papers_if_needed()
        return app_session.db_collections[DBCollection.SCIENCE_PAPERS]
    else:
        raise ValueError(f"Unknown document set: {document_set}")


def display_prompt_editor(key_suffix: str, document_set: RagDocumentSet, include_all_relevant_meta_in_system_prompt: bool = False) -> str:
    ROLE: str = st.text_input("Role", key=f"rag_role_{key_suffix}")
    INSTRUCTION: str = st.text_input("Instruction", key=f"rag_instruction_{key_suffix}")
    OUTPUT_FORMAT: str = st.text_input("Output format", key=f"rag_output_format_{key_suffix}")

    INPUT: str  # input already provided by variable question

    # attributes of document.meta correspond with the fields of the VDIDoc class
    # Tip: You can find the price field name in the class VDIDoc (use the browser search or hyperlinks of exercise #2)
    CONTEXT = get_default_document_set_context_prompt(document_set, include_all_relevant_meta_in_system_prompt)

    CONTEXT: str = st.text_area("Context", CONTEXT, height=200, key=f"rag_context_{key_suffix}")

    return f"""
    {ROLE}
    {INSTRUCTION}
    Context:
    {CONTEXT}
    {OUTPUT_FORMAT}
    Question: {{{{question}}}}
    Answer:
    """


def execute_rag(question: str, prompt: str, client: openai.OpenAI | openai.AzureOpenAI, collection, n_docs: int = 5) -> tuple[list[Document], str]:
    with st.spinner("Retrieve documents..."):
        # Use ChromaDB to retrieve documents
        results = collection.query(
            query_texts=[question],
            n_results=n_docs
        )
        retrieved_docs = chromadb_results_to_documents(results)

    with st.spinner("Generate solution..."):
        template = Template(prompt)
        rendered_prompt = template.render(documents=retrieved_docs, question=question)
        response = llm_call(client, system_prompt="", user_prompt=rendered_prompt)

    return retrieved_docs, response


def display_rag_results(docs: list[Document], response: str):
    st.divider()
    st.write("#### Documents")
    tabs = st.tabs([f"Document #{i + 1}" for i in range(len(docs))])
    for i, doc in enumerate(docs):
        with tabs[i]:
            st.write(f"##### Document #{i + 1}")
            st.text("Embedding Input Text\n" + doc.content)
            st.text("Document Meta\n")
            st.write(doc.meta)
    st.divider()
    st.write("#### Answer")
    st.write(response)


def display_exercise_rag(task_text: str,
                         doc_validation_fn: Callable[[list[Document]], bool] | None = None,
                         rag_response_validation_fn: Callable[[list[Document], str], bool] | None = None,
                         include_all_relevant_meta_in_system_prompt: bool = False,
                         question: str | None = None
                         ) -> bool | None:
    client = st.session_state[APP_SESSION_KEY].client
    display_task_text_field(task_text)
    doc_set = RagDocumentSet(st.session_state.get(DATA_SELECTION_SESSION_KEY))

    # Get ChromaDB collection
    collection = get_chromadb_collection(doc_set)

    prompt = display_prompt_editor(hash_text(task_text), doc_set, include_all_relevant_meta_in_system_prompt)
    st.write("#### System prompt")
    st.text(prompt)

    n_docs = st.number_input("Number of context documents", value=5)

    question = st.text_input("Question:", key=f"rag_question_{hash_text(task_text)}", value=question)

    if st.button("Run RAG pipeline", key=f"rag_run_button_{hash_text(task_text)}"):
        retrieved_docs, response = execute_rag(question, prompt, client, collection, n_docs=n_docs)
        display_rag_results(retrieved_docs, response)
        if doc_validation_fn is not None:
            return doc_validation_fn(retrieved_docs)
        if rag_response_validation_fn is not None:
            return rag_response_validation_fn(retrieved_docs, response)
    return False


def validate_exercise_vdi_docs_1_fn(retrieved_docs: list[Document]):
    return any([doc for doc in retrieved_docs if doc.meta["title"] == "Power-to-X - CO2 -Bereitstellung"])

def validate_exercise_science_papers_1_fn(retrieved_docs: list[Document]):
    electricity_paper_dois = ["10.1007/978-3-030-66661-3_7", "10.1145/3230712", "10.1287/isre.2021.1098", "10.1016/j.dss.2022.113895"]
    return any([doc for doc in retrieved_docs if doc.meta.get("doi") in electricity_paper_dois])


def validate_exercise_vdi_docs_2_fn(retrieved_docs: list[Document], response: str):
    if any([doc for doc in retrieved_docs if doc.meta["title"] == "Power-to-X - CO2 -Bereitstellung"]):
        if "113.7" in response or "113,7" in response:
            return True

def validate_exercise_science_papers_2_fn(retrieved_docs: list[Document], response: str):
    electricity_paper_creators = ["Jurica Babic", "Vedran Podobnik", "Clemens van Dinther", "Christoph M. Flath",
                                  "Johannes Gaerttner", "Julian Huber", "Esther Mengelkamp","Alexander Schuller",
                                  "Philipp Staudt", "Anke Weidlich", "Wolfgang Ketter", "John Collins",
                                  "Maytal Saar-Tsechansky", "Ori Marom"]
    if any([creator in response for creator in electricity_paper_creators]):
        return True

def validate_exercise_vdi_docs_3_fn(retrieved_docs: list[Document], response: str):
    # Remove unwanted prefixes
    json_string = response.strip()
    if json_string.startswith("```json"):
        json_string = json_string[len("```json"):].strip()
    if json_string.startswith("```"):
        json_string = json_string[len("```"):].strip()
    if json_string.endswith("```"):
        json_string = json_string[:-len("```")].strip()
    try:
        json.loads(json_string)  # Try to parse the JSON string
        return True
    except (ValueError, TypeError):  # Catch parsing errors
        return False


def validate_exercise_science_papers_3_fn(retrieved_docs: list[Document], response: str, task: str):
    client = st.session_state[APP_SESSION_KEY].client
    system_prompt = f"""You are an exercise instructor,
Evaluate whether the following answer delimited by ``` fulfills the task "{task}". 
The answer to the question is in the broadest sense "energy markets/smart grids" and "information systems for mobility".
Answer with "yes" if the task is solved and "no" if not.
Do not include any explanation."""
    llm_answer = llm_call(client, system_prompt=system_prompt, user_prompt=f'answer: ```{response}```', model="gpt-4o-mini")
    return "yes" in llm_answer


def validate_exercise_vdi_docs_4_fn(retrieved_docs: list[Document], response: str, task: str):
    client = st.session_state[APP_SESSION_KEY].client
    system_prompt = f"""You are an exercise instructor,
Evaluate whether the following answer delimited by ``` fulfills the task "{task}". 
The answer to the question should be that no document contains the relevant information..
Answer with "yes" if the task is solved and "no" if not.
Do not include any explanation."""
    llm_answer = llm_call(client, system_prompt=system_prompt, user_prompt=f'answer: ```{response}```', model="gpt-4o-mini")
    return "yes" in llm_answer


def display_data_selection():
    def _change_module_in_session():
        doc_set = st.session_state[DATA_SELECTION_SESSION_KEY]
        app_session: AppSession = st.session_state[APP_SESSION_KEY]
        app_session.modules[ModuleNames.RETRIEVAL_AUGMENTED_GENERATION] = get_module_rag(7)[doc_set]

    available_document_sets = RagDocumentSet.to_list()
    available_document_sets.remove(RagDocumentSet.RESUMES)
    if len(available_document_sets) == 0:
        st.error("Could not find any available document sets")
    st.selectbox("Documents", available_document_sets,
                 key=DATA_SELECTION_SESSION_KEY,
                 on_change=_change_module_in_session)


def get_module_rag_vdi_exercises() -> list[Callable[[], bool | None]]:
    task_4 = "Prevent the LLM from passing on false information ('Gravitationswellen-Resonanz' is not part of the dataset, nor is it used for aircraft propulsion system)"
    return [partial(display_exercise_rag,
                    task_text="Find at least one VDI document with the topic CO2 reduction",
                    doc_validation_fn=validate_exercise_vdi_docs_1_fn),
            partial(display_exercise_rag,
                    task_text='Add the price meta information to the context and extract the price of the document "Power-to-X - CO2 -Bereitstellung"',
                    rag_response_validation_fn=validate_exercise_vdi_docs_2_fn),
            partial(display_exercise_rag,
                    task_text='Return the output in JSON format',
                    rag_response_validation_fn=validate_exercise_vdi_docs_3_fn,
                    include_all_relevant_meta_in_system_prompt=True),
            partial(display_exercise_rag,
                    task_text=task_4,
                    question="Erkläre mir die Funktionsweise eines neuartigen Antriebsystems für Flugzeuge, das auf der Technologie der 'Gravitationswellen-Resonanz' basiert.",
                    rag_response_validation_fn=partial(validate_exercise_vdi_docs_4_fn,
                                                       task=task_4
                                                       ))
            ]


def get_module_rag_science_papers_exercises() -> list[Callable[[], bool | None]]:
    task_5 = 'Which two fields of research is Wolfgang Ketter working on?'
    task_4 = "Prevent the LLM from passing on false information ('Gravitationswellen-Resonanz' is not part of the dataset, nor is it used for aircraft propulsion system)"
    return [partial(display_exercise_rag,
                    task_text="Find at least one Paper with the topic electricity market",
                    doc_validation_fn=validate_exercise_science_papers_1_fn),
            partial(display_exercise_rag,
                    task_text='Add the creator information to the context and return the creators of electricity market papers',
                    rag_response_validation_fn=validate_exercise_science_papers_2_fn),
            partial(display_exercise_rag,
                    task_text='Return the output in JSON format',
                    rag_response_validation_fn=validate_exercise_vdi_docs_3_fn),
            partial(display_exercise_rag,
                    task_text=task_4,
                    question="Erkläre mir die Funktionsweise eines neuartigen Antriebsystems für Flugzeuge, das auf der Technologie der 'Gravitationswellen-Resonanz' basiert.",
                    rag_response_validation_fn=partial(validate_exercise_vdi_docs_4_fn,
                                                       task=task_4
                                                       )),
            partial(display_exercise_rag,
                    task_text=task_5,
                    rag_response_validation_fn=partial(validate_exercise_science_papers_3_fn,
                                                       task=task_5,
                                                       ),
                    include_all_relevant_meta_in_system_prompt=True)
            ]


def get_module_view(exercises: list[Callable[[], bool | None]], session_key: str, module_nr: int) -> ModuleView:
    return ModuleView(
        title="Retrieval Augmented Generation",
        description="""### What is Retrieval Augmented Generation?
Retrieval-Augmented Generation (RAG) boosts AI's accuracy and adaptability by merging pre-trained language models with real-time data retrieval from external sources (e.g., documents, databases). 
It generates context-aware responses—think customer support, research, or content tasks—by dynamically pulling current or domain-specific information, reducing errors and ensuring relevance without retraining. 
A practical, efficient solution for businesses needing trustworthy, up-to-date AI outputs.""",
        module_nr=module_nr,
        session_key=session_key,
        data_selection_fn=display_data_selection,
        exercises=exercises,
        render_exercises_with_level_selectbox=True
    )


def get_module_rag(module_nr: int) -> dict[RagDocumentSet, ModuleView]:
    session_key=f"module_{module_nr}"
    return {
        RagDocumentSet.VDI_DOCS: get_module_view(get_module_rag_vdi_exercises(), session_key=f"{session_key}_{RagDocumentSet.VDI_DOCS}", module_nr=module_nr),
        RagDocumentSet.SCIENCE_PAPERS: get_module_view(get_module_rag_science_papers_exercises(), session_key=f"{session_key}_{RagDocumentSet.SCIENCE_PAPERS}", module_nr=module_nr)
    }
