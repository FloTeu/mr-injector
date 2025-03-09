import chromadb
import streamlit as st

from mr_injector.backend.db import init_chroma_db_client


@st.cache_resource
def init_chroma_db_client_cached() -> chromadb.PersistentClient:
    return init_chroma_db_client()
