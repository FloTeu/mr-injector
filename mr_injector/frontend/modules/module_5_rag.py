import json
from functools import partial
from pathlib import Path
from typing import Callable
from jinja2 import Template

import openai
import streamlit as st
from haystack.document_stores.in_memory import InMemoryDocumentStore
from openai import OpenAI

from haystack.components.builders import PromptBuilder
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack import Document

from mr_injector.backend.models.documents import RagDocumentSet
from mr_injector.backend.openai import llm_call
from mr_injector.backend.rag import get_retrieval_pipeline, \
    create_haystack_vdi_documents, create_haystack_bibtex_citations, get_default_document_set_context_prompt
from mr_injector.backend.utils import hash_text
from mr_injector.frontend.modules.main import ModuleView

MODULE_NR = 5
SESSION_KEY = f"module_{MODULE_NR}"
DATA_SELECTION_SESSION_KEY = "rag_document_set_selectbox"


@st.cache_data
def get_document_store(file_dir: Path) -> InMemoryDocumentStore:
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
    doc_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
    doc_embedder.warm_up()
    docs_with_embeddings = doc_embedder.run(docs)
    document_store.write_documents(docs_with_embeddings["documents"])
    return document_store


def display_prompt_editor(key_suffix: str, document_set: RagDocumentSet) -> str:
    ROLE: str = st.text_input("Role", key=f"rag_role_{key_suffix}")
    INSTRUCTION: str = st.text_input("Instruction", key=f"rag_instruction_{key_suffix}")
    OUTPUT_FORMAT: str = st.text_input("Output format", key=f"rag_output_format_{key_suffix}")

    INPUT: str  # input already provided by variable question

    # attributes of document.meta correspond with the fields of the VDIDoc class
    # Tip: You can find the price field name in the class VDIDoc (use the browser search or hyperlinks of exercise #2)
    CONTEXT = get_default_document_set_context_prompt(document_set)

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
        response = llm_call(client, "", rendered_prompt)

    return retrieved_docs, response


def display_rag_results(docs: list[Document], response: str):
    st.divider()
    st.write("#### Documents")
    tabs = st.tabs([f"Document #{i + 1}" for i in range(len(docs))])
    for i, doc in enumerate(docs):
        with tabs[i]:
            st.write(f"##### Document #{i + 1}")
            st.text("Text\n" + doc.content)
            st.text("Document Meta\n")
            st.write(doc.meta)
    st.divider()
    st.write("#### Answer")
    st.write(response)


def display_exercise_rag(client: OpenAI,
                         task_text: str,
                         doc_validation_fn: Callable[[list[Document]], bool] | None = None,
                         rag_response_validation_fn: Callable[[list[Document], str], bool] | None = None
                         ) -> bool | None:
    st.write(task_text)
    doc_set = RagDocumentSet(st.session_state.get(DATA_SELECTION_SESSION_KEY))
    document_store = get_document_store(Path(doc_set.get_path()))

    prompt = display_prompt_editor(hash_text(task_text), doc_set)
    st.write("#### System prompt")
    st.text(prompt)

    # create final RAG pipeline
    retrieval_pipeline = get_retrieval_pipeline(
        SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"),
        InMemoryEmbeddingRetriever(document_store, top_k=5))

    question = st.text_input("Question:", key=f"rag_question_{hash_text(task_text)}")

    if st.button("Run RAG pipeline", key=f"rag_run_button_{hash_text(task_text)}"):
        retrieved_docs, response = execute_rag(question, prompt, client, retrieval_pipeline)
        display_rag_results(retrieved_docs, response)
        if doc_validation_fn is not None:
            return doc_validation_fn(retrieved_docs)
        if rag_response_validation_fn is not None:
            return rag_response_validation_fn(retrieved_docs, response)
    return False


def exercise_1_fn(retrieved_docs: list[Document]):
    return any([doc for doc in retrieved_docs if doc.meta["title"] == "Power-to-X - CO2 -Bereitstellung"])


def exercise_2_fn(retrieved_docs: list[Document], response: str):
    if any([doc for doc in retrieved_docs if doc.meta["title"] == "Power-to-X - CO2 -Bereitstellung"]):
        if "113.7" in response or "113,7" in response:
            return True


def exercise_3_fn(retrieved_docs: list[Document], response: str):
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


def display_data_selection():
    available_document_sets = RagDocumentSet.to_list()
    if len(available_document_sets) == 0:
        st.error("Could not find any available document sets")
    st.selectbox("Documents", available_document_sets, key=DATA_SELECTION_SESSION_KEY)


def get_module_rag_vdi_exercises(client: OpenAI) -> list[Callable[[], bool | None]]:
    return [partial(display_exercise_rag,
                    client=client,
                    task_text="**Task**: Find at least one VDI document with the topic CO2 reduction",
                    doc_validation_fn=exercise_1_fn),
            partial(display_exercise_rag,
                    client=client,
                    task_text='**Task**: Add the price meta information to the context and extract the price of the document "Power-to-X - CO2 -Bereitstellung"',
                    rag_response_validation_fn=exercise_2_fn),
            partial(display_exercise_rag,
                    client=client,
                    task_text='**Task**: Return the output in JSON format',
                    rag_response_validation_fn=exercise_3_fn)
            ]


def get_module_rag_science_papers_exercises(client: OpenAI) -> list[Callable[[], bool | None]]:
    return [partial(display_exercise_rag,
                    client=client,
                    task_text="**Task**: Find at least one Paper with the topic mobility",
                    doc_validation_fn=exercise_1_fn),
            partial(display_exercise_rag,
                    client=client,
                    task_text='**Task**: Add the price meta information to the context and extract the price of the document "Power-to-X - CO2 -Bereitstellung"',
                    rag_response_validation_fn=exercise_2_fn),
            partial(display_exercise_rag,
                    client=client,
                    task_text='**Task**: Return the output in JSON format',
                    rag_response_validation_fn=exercise_3_fn)
            ]


def get_module_view(exercises: list[Callable[[], bool | None]], session_key: str) -> ModuleView:
    return ModuleView(
        title="Retrieval Augmented Generation",
        description="""### What is Retrieval Augmented Generation?""",
        module_nr=MODULE_NR,
        session_key=session_key,
        data_selection_fn=display_data_selection,
        exercises=exercises,
        render_exercises_with_level_selectbox=True
    )


def get_module_rag(client: OpenAI) -> dict[RagDocumentSet, ModuleView]:
    return {
        RagDocumentSet.VDI_DOCS: get_module_view(get_module_rag_vdi_exercises(client), session_key=f"{SESSION_KEY}{RagDocumentSet.VDI_DOCS}"),
        RagDocumentSet.SCIENCE_PAPERS: get_module_view(get_module_rag_science_papers_exercises(client), session_key=f"{SESSION_KEY}{RagDocumentSet.SCIENCE_PAPERS}")
    }
