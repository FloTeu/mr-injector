import os
import json
from typing import List
from haystack import Document
from haystack import Pipeline

from mr_injector.backend.models.documents import VDIDoc


def create_haystack_vdi_documents(directory_path: str) -> List[Document]:
    """
    Iterates over all JSON files in the specified directory and creates a list of Haystack 2.0 Documents.

    Args:
    directory_path (str): The path to the directory containing JSON files.

    Returns:
    List[Document]: A list of Haystack Document objects.
    """
    documents = []
    # Iterate over each file in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            # Open and load the JSON file
            with open(file_path, 'r', encoding='utf-8') as file:
                vdi_doc = VDIDoc(**json.load(file))
                doc = Document(content=vdi_doc.abstract, meta=vdi_doc.dict())
                documents.append(doc)
    return documents



def get_rag_pipeline(text_embedder, retriever, prompt_builder, generator) -> Pipeline:
  rag_pipeline = Pipeline()
  # Add components to your pipeline
  rag_pipeline.add_component("text_embedder", text_embedder)
  rag_pipeline.add_component("retriever", retriever)
  rag_pipeline.add_component("prompt_builder", prompt_builder)
  rag_pipeline.add_component("llm", generator)

  # Now, connect the components to each other
  rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
  rag_pipeline.connect("retriever", "prompt_builder.documents")
  rag_pipeline.connect("prompt_builder", "llm")

  return rag_pipeline

def get_retrieval_pipeline(text_embedder, retriever) -> Pipeline:
  rag_pipeline = Pipeline()
  # Add components to your pipeline
  rag_pipeline.add_component("text_embedder", text_embedder)
  rag_pipeline.add_component("retriever", retriever)

  # Now, connect the components to each other
  rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

  return rag_pipeline

