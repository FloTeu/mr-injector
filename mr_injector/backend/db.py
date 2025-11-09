import zipfile
from contextlib import suppress

import chromadb
import requests
from chromadb import EmbeddingFunction, Documents, Embeddings, Client as ChromaDBClient
from chromadb.errors import UniqueConstraintError
from openai import OpenAI, AzureOpenAI, embeddings

from mr_injector.backend.models.documents import Document
from mr_injector.backend.utils import get_root_dir


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

def create_chromadb_collection(client: ChromaDBClient, col_name: str, embedding_function, ensure_new: bool = False) -> chromadb.Collection:
    # ensure collection does not already exist
    if ensure_new:
        delete_chromadb_collection(client, col_name)

    # Create or get existing collection
    try:
        return client.get_or_create_collection(
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
        print(f"Adding documents {i} to {min(i + batch_size, len(docs))} to collection {collection.name}")
        end_idx = min(i + batch_size, len(docs))
        try:
            collection.add(
                documents=[d.content for d in docs[i:end_idx]],
                metadatas=[d.meta for d in docs[i:end_idx]],
                ids=[d.id for d in docs[i:end_idx]]
            )
        except Exception as e:
            print(f"Error adding documents to collection: {e}")
            continue

def semantic_search(collection: chromadb.Collection, query: str, n_results: int = 2):
    """Perform semantic search on the collection"""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results

def download_chinebook_db():
    url = "https://storage.googleapis.com/inovex-prompt-engineering-seminar/chinook.zip"

    response = requests.get(url)
    files_dir = get_root_dir() / f"files"
    zip_file_path = files_dir / f"chinook.zip"

    # Save the ZIP file to the specified path
    with open(zip_file_path, 'wb') as f:
        f.write(response.content)

    # Unpack the ZIP file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(files_dir)

def download_resume_csv():
    url = "https://storage.googleapis.com/inovex-prompt-engineering-seminar/resumes.csv"
    response = requests.get(url)
    files_dir = get_root_dir() / f"files"
    resume_file_path = files_dir / f"resumes.csv"

    # Save the ZIP file to the specified path
    with open(resume_file_path, 'wb') as f:
        f.write(response.content)

