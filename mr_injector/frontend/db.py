import chromadb
import streamlit as st

from mr_injector.backend.db import init_chroma_db_client, OpenAIEmbeddingFunction, create_chromadb_collection, \
    add_to_collection
from mr_injector.backend.models.db import DBCollection
from mr_injector.backend.models.documents import RagDocumentSet
from mr_injector.backend.rag import extract_resume_documents
from mr_injector.frontend.session import APP_SESSION_KEY


@st.cache_resource
def init_chroma_db_client_cached() -> chromadb.PersistentClient:
    model_client = st.session_state[APP_SESSION_KEY].client
    if model_client is None:
        raise ValueError("model client is required")
    db_client = init_chroma_db_client()
    init_db_cols(db_client, model_client)

    return db_client


def init_db_cols(db_client, model_client):
    embedding_function = OpenAIEmbeddingFunction(client=model_client)
    # create collection
    resume_col = create_chromadb_collection(db_client, DBCollection.RESUMES, embedding_function, ensure_new=False)
    vdi_doc_col = create_chromadb_collection(db_client, DBCollection.VDI_DOCS, embedding_function, ensure_new=False)
    science_paper_col = create_chromadb_collection(db_client, DBCollection.SCIENCE_PAPERS, embedding_function,
                                                   ensure_new=False)
    # fill up collection
    if resume_col.count() == 0:
        file_path = RagDocumentSet.RESUMES.get_path()
        docs = extract_resume_documents(file_path)
        add_to_collection(docs, resume_col)
    st.session_state[APP_SESSION_KEY].db_collections = {
        DBCollection.RESUMES: resume_col,
        DBCollection.VDI_DOCS: vdi_doc_col,
        DBCollection.SCIENCE_PAPERS: science_paper_col
    }
