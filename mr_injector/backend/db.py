from contextlib import suppress

import chromadb
from chromadb.errors import InvalidCollectionException

from mr_injector.backend.models.documents import Document


def init_chroma_db_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path="chroma_db")

def delete_chromadb_collection(client: chromadb.Client(), col_name: str):
    with suppress(ValueError):
        client.delete_collection(name=col_name)

def create_chromadb_collection(client: chromadb.Client(), col_name: str, embedding_function) -> chromadb.Collection:
    # ensure collection does not already exist
    delete_chromadb_collection(client, col_name)

    # Create or get existing collection
    return client.create_collection(
        name=col_name,
        embedding_function=embedding_function
    )

def add_to_collection(docs: list[Document], collection: chromadb.Collection):
    """Add documents to collection in batches"""
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        end_idx = min(i + batch_size, len(docs))
        collection.add(
            documents=[d.content for d in docs[i:end_idx]],
            metadatas=[d.meta for d in docs[i:end_idx]],
            ids=[d.id for d in docs[i:end_idx]]
        )

def semantic_search(collection: chromadb.Collection, query: str, n_results: int = 2):
    """Perform semantic search on the collection"""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results