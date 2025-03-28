from contextlib import suppress

import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.errors import UniqueConstraintError
from openai import OpenAI, AzureOpenAI, embeddings

from mr_injector.backend.models.documents import Document

class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __init__(self, client: OpenAI | AzureOpenAI, model: str = "text-embedding-ada-002"):
        self.client = client
        self.model = model

    def __call__(self, input: Documents) -> Embeddings:
        # embed the documents somehow
        embeddings = []
        for doc in input:
            response = self.client.embeddings.create(
                input=doc,
                model=self.model
            )
            embeddings.append(response.data[0].embedding)
        return embeddings


def init_chroma_db_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path="chroma_db")

def delete_chromadb_collection(client, col_name: str):
    with suppress(ValueError):
        client.delete_collection(name=col_name)

def create_chromadb_collection(client, col_name: str, embedding_function, ensure_new: bool = False) -> chromadb.Collection:
    # ensure collection does not already exist
    if ensure_new:
        delete_chromadb_collection(client, col_name)

    # Create or get existing collection
    try:
        return client.create_collection(
            name=col_name,
            embedding_function=embedding_function
        )
    except UniqueConstraintError:
        return client.get_collection(
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



