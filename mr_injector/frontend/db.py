import chromadb
import streamlit as st

from mr_injector.backend.db import init_chroma_db_client, OpenAIEmbeddingFunction, create_chromadb_collection, \
    add_to_collection, download_resume_csv
from mr_injector.backend.models.db import DBCollection
from mr_injector.backend.models.documents import RagDocumentSet
from mr_injector.backend.rag import extract_resume_documents, create_vdi_documents, create_bibtex_citation_documents
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

    # Fill up RESUMES collection
    file_path = RagDocumentSet.RESUMES.get_path()
    if not file_path.exists():
        print("Downloading resume CSV file...")
        download_resume_csv()

    if resume_col.count() == 0 and file_path.exists():
        docs = extract_resume_documents(file_path)
        add_to_collection(docs, resume_col)

    # Fill up VDI_DOCS collection
    vdi_path = RagDocumentSet.VDI_DOCS.get_path()
    if vdi_doc_col.count() == 0 and vdi_path.exists():
        docs = create_vdi_documents(vdi_path)
        add_to_collection(docs, vdi_doc_col)
        print(f"Populated VDI_DOCS collection with {len(docs)} documents")

    # SCIENCE_PAPERS collection is created but NOT populated here
    # It will be populated lazily when first accessed (see populate_science_papers_if_needed)

    st.session_state[APP_SESSION_KEY].db_collections = {
        DBCollection.RESUMES: resume_col,
        DBCollection.VDI_DOCS: vdi_doc_col,
        DBCollection.SCIENCE_PAPERS: science_paper_col
    }


def populate_science_papers_if_needed():
    """
    Lazily populate the SCIENCE_PAPERS collection when first accessed.
    This is called from the RAG module when science papers exercises are accessed.
    """
    app_session = st.session_state[APP_SESSION_KEY]
    science_paper_col = app_session.db_collections[DBCollection.SCIENCE_PAPERS]

    # Check if already populated
    if science_paper_col.count() == 0:
        science_path = RagDocumentSet.SCIENCE_PAPERS.get_path()
        if science_path.exists():
            with st.spinner("Loading science papers into database... (this only happens once)"):
                docs = create_bibtex_citation_documents(science_path)
                add_to_collection(docs, science_paper_col)
                print(f"Populated SCIENCE_PAPERS collection with {len(docs)} documents")
                st.success(f"Loaded {len(docs)} science paper documents!")
