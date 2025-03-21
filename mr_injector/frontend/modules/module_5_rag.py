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

from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder, OpenAIDocumentEmbedder, AzureOpenAIDocumentEmbedder, OpenAITextEmbedder, AzureOpenAITextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack import Document
from haystack.utils import Secret
from haystack.document_stores.in_memory import InMemoryDocumentStore

from mr_injector.backend.models.documents import RagDocumentSet
from mr_injector.backend.llm import llm_call
from mr_injector.backend.rag import get_retrieval_pipeline, \
    create_haystack_vdi_documents, create_haystack_bibtex_citations, get_default_document_set_context_prompt
from mr_injector.backend.utils import hash_text, booleanize
from mr_injector.frontend.css import get_exercise_styling
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY, ModuleNames, AppSession

MODULE_NR = 5
SESSION_KEY = f"module_{MODULE_NR}"
DATA_SELECTION_SESSION_KEY = "rag_document_set_selectbox"

DOCUMENT_STORE_CACHE: dict[RagDocumentSet, InMemoryDocumentStore] = {}

def get_document_store(file_dir: Path, client: OpenAI | AzureOpenAI) -> InMemoryDocumentStore:
    # Database/Index Creation
    document_store = InMemoryDocumentStore()
    # all vdi documents in haystack format
    docs: list[Document] = []
    if RagDocumentSet.SCIENCE_PAPERS in str(file_dir):
        docs = create_haystack_bibtex_citations(file_dir)
    elif RagDocumentSet.VDI_DOCS in str(file_dir):
        docs = create_haystack_vdi_documents(file_dir)
    print("Number of documents", len(docs))
    # create embeddings
    doc_embedder = get_haystack_embedding_model(client)
    docs_with_embeddings = doc_embedder.run(docs)
    document_store.write_documents(docs_with_embeddings["documents"])
    return document_store


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


def execute_rag(question, prompt, client: openai.OpenAI | openai.AzureOpenAI, retrieval_pipeline) -> tuple[
    list[Document], str]:
    with st.spinner("Retrieve documents..."):
        retrieved_docs = retrieval_pipeline.run({"text_embedder": {"text": question}})["retriever"]["documents"]

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


def get_haystack_embedding_model(client: OpenAI | AzureOpenAI, text_embedder: bool = False) -> OpenAIDocumentEmbedder | OpenAITextEmbedder | AzureOpenAIDocumentEmbedder | AzureOpenAITextEmbedder | SentenceTransformersTextEmbedder |SentenceTransformersDocumentEmbedder:
    if booleanize(os.environ.get("USE_OPEN_AI_EMBEDDINGS", False)):
        if isinstance(client, AzureOpenAI):
            if text_embedder:
                embedder = AzureOpenAITextEmbedder(api_key=Secret.from_token(client.api_key), azure_deployment="text-embedding-ada-002", azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", None))
            else:
                embedder = AzureOpenAIDocumentEmbedder(api_key=Secret.from_token(client.api_key), azure_deployment="text-embedding-ada-002", azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", None))
        elif isinstance(client, OpenAI):
            if text_embedder:
                embedder = OpenAITextEmbedder(api_key=Secret.from_token(client.api_key), model="text-embedding-ada-002")
            else:
                embedder = OpenAIDocumentEmbedder(api_key=Secret.from_token(client.api_key), model="text-embedding-ada-002")
        else:
            raise ValueError("client not known")
    else:
        if text_embedder:
            embedder = SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"),
        else:
            embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        embedder.warm_up()
    return embedder


def display_exercise_rag(task_text: str,
                         doc_validation_fn: Callable[[list[Document]], bool] | None = None,
                         rag_response_validation_fn: Callable[[list[Document], str], bool] | None = None,
                         include_all_relevant_meta_in_system_prompt: bool = False,
                         question: str | None = None
                         ) -> bool | None:
    client = st.session_state[APP_SESSION_KEY].client
    display_task_text_field(task_text)
    doc_set = RagDocumentSet(st.session_state.get(DATA_SELECTION_SESSION_KEY))
    if doc_set in DOCUMENT_STORE_CACHE:
        document_store = DOCUMENT_STORE_CACHE[doc_set]
    else:
        with st.spinner("Creating document index..."):
            document_store = get_document_store(Path(doc_set.get_path()), client)
        DOCUMENT_STORE_CACHE[doc_set] = document_store

    prompt = display_prompt_editor(hash_text(task_text), doc_set, include_all_relevant_meta_in_system_prompt)
    st.write("#### System prompt")
    st.text(prompt)

    n_docs = st.number_input("Number of context documents", value=5)

    # create final RAG pipeline
    retrieval_pipeline = get_retrieval_pipeline(
        get_haystack_embedding_model(client, text_embedder=True),
        #SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"),
        InMemoryEmbeddingRetriever(document_store, top_k=n_docs))

    question = st.text_input("Question:", key=f"rag_question_{hash_text(task_text)}", value=question)

    if st.button("Run RAG pipeline", key=f"rag_run_button_{hash_text(task_text)}"):
        retrieved_docs, response = execute_rag(question, prompt, client, retrieval_pipeline)
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
    return any([doc for doc in retrieved_docs if doc.meta["doi"] in electricity_paper_dois])


def validate_exercise_vdi_docs_2_fn(retrieved_docs: list[Document], response: str):
    if any([doc for doc in retrieved_docs if doc.meta["title"] == "Power-to-X - CO2 -Bereitstellung"]):
        if "117.1" in response or "117,1" in response:
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
        app_session.modules[ModuleNames.RETRIEVAL_AUGMENTED_GENERATION] = get_module_rag()[doc_set]

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


def get_module_view(exercises: list[Callable[[], bool | None]], session_key: str) -> ModuleView:
    return ModuleView(
        title="Retrieval Augmented Generation",
        description="""### What is Retrieval Augmented Generation?
Retrieval-Augmented Generation (RAG) boosts AI's accuracy and adaptability by merging pre-trained language models with real-time data retrieval from external sources (e.g., documents, databases). 
It generates context-aware responses—think customer support, research, or content tasks—by dynamically pulling current or domain-specific information, reducing errors and ensuring relevance without retraining. 
A practical, efficient solution for businesses needing trustworthy, up-to-date AI outputs.""",
        module_nr=MODULE_NR,
        session_key=session_key,
        data_selection_fn=display_data_selection,
        exercises=exercises,
        render_exercises_with_level_selectbox=True
    )


def get_module_rag() -> dict[RagDocumentSet, ModuleView]:
    return {
        RagDocumentSet.VDI_DOCS: get_module_view(get_module_rag_vdi_exercises(), session_key=f"{SESSION_KEY}_{RagDocumentSet.VDI_DOCS}"),
        RagDocumentSet.SCIENCE_PAPERS: get_module_view(get_module_rag_science_papers_exercises(), session_key=f"{SESSION_KEY}_{RagDocumentSet.SCIENCE_PAPERS}")
    }
