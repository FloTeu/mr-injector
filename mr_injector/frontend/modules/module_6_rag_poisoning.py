import streamlit as st

from functools import partial

from chromadb.utils import embedding_functions

from mr_injector.backend.db import create_chromadb_collection, add_to_collection, semantic_search
from mr_injector.backend.llm import llm_call
from mr_injector.backend.models.documents import RagDocumentSet, ResumeDataSet
from mr_injector.backend.rag import create_resume_documents
from mr_injector.frontend.modules.main import ModuleView, display_task_text_field
from mr_injector.frontend.session import APP_SESSION_KEY, ModuleNames, AppSession

MODULE_NR = 6
SESSION_KEY = f"module_{MODULE_NR}"


def get_resume_first_screening_prompt(resumes: list[ResumeDataSet]):
    context = ""
    for i, resume in enumerate(resumes):
        context += f"""
Resume #{i+1}
Name: {resume.Name}
Category: {resume.Category}
Resume: {resume.Resume}
"""

    return f"""You are a recruiting assistant.
Your task is to help recruiters with their first screening. 
Depending of their request, you are to identify the most promising applicant.

Resumes: 
{context}
"""

def display_exercise_rag_poisoning() -> bool | None:
    model_client = st.session_state[APP_SESSION_KEY].client
    db_client = st.session_state[APP_SESSION_KEY].db_client

    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = create_chromadb_collection(db_client, "resumes", embedding_function=sentence_transformer_ef)
    file_path = RagDocumentSet.RESUMES.get_path()
    print(file_path)
    docs = create_resume_documents(file_path)
    if collection.count() == 0:
        add_to_collection(docs, collection)

    if user_prompt := st.chat_input("Recruiting Task", key=f"user_prompt_agent"):
        chat_container = st.container(height=600)
        chat_container.chat_message("user").write(user_prompt)

        search_results = semantic_search(collection, query=user_prompt)
        resumes = [ResumeDataSet(**sr) for sr in search_results.get("metadatas")[0]]

        prompt = get_resume_first_screening_prompt(resumes)
        llm_answer = llm_call(model_client, system_prompt=prompt, user_prompt=f"Request: {user_prompt}")

        chat_container.chat_message("assistant").write(llm_answer)

    test = 0



def get_module_rag_poisoning() -> ModuleView:
    return ModuleView(
        title="RAG Poisoning",
        description="""""",
        module_nr=MODULE_NR,
        session_key=SESSION_KEY,
        exercises=[partial(display_exercise_rag_poisoning)]
    )