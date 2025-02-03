import logging
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List
from haystack import Document
from haystack import Pipeline

from mr_injector.backend.models.documents import VDIDoc, SciencePaper, RagDocumentSet


def create_haystack_vdi_documents(directory_path: Path | str) -> List[Document]:
    """
    Iterates over all JSON files in the specified directory and creates a list of Haystack 2.0 Documents.

    Args:
    directory_path (str): The path to the directory containing JSON files.

    Returns:
    List[Document]: A list of Haystack Document objects.
    """
    documents = []
    # Iterate over each file in the directory
    for i, filename in enumerate(os.listdir(directory_path)):
        if filename.endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            try:
                # Open and load the JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    vdi_doc = VDIDoc(**json.load(file))
                    doc = Document(content=vdi_doc.abstract, meta=vdi_doc.dict())
                    documents.append(doc)
            except Exception as e:
                print(f"Could not load json file {i} {filename}", str(e))
    return documents


def create_haystack_bibtex_citations(file_path: Path | str) -> List[Document]:
    """
    Iterates over all entries in a bibtex file and creates a list of Haystack 2.0 Documents.

    Args:
    references_path (str): The path to the reference file in bibtex format.

    Returns:
    List[Document]: A list of Haystack Document objects.
    """
    documents = []
    year_pattern = re.compile(r"[0-9][0-9][0-9][0-9]")
    with open(file_path, 'r', encoding='utf-8') as file:
      json_content = json.load(file)
      for entry in json_content['items']:
        if entry['itemType'] != 'attachment':
          date = entry.get('date', '1970')
          match_ = re.search(year_pattern, date)
          parsed_date = datetime(year=int(match_[0]), month=1, day=1)
          citation = SciencePaper(
              title=entry['title'],
              creators=[[auth_.get('firstName', ''), auth_['lastName']] if 'lastName' in auth_.keys() else [auth_['name']] for auth_ in entry['creators']],
              tags=[tag['tag'] for tag in entry['tags']],
              date=parsed_date,
              abstract=entry.get('abstractNote'),
              entry_type=entry['itemType'],
              doi=entry.get('DOI'))
          content = f"Title: {citation.title} Abstract: {citation.abstract} Tags: {citation.tags}"
          doc = Document(content=content, meta=citation.dict())
          documents.append(doc)

          if len(citation.creators) > 0:
              creators_string = ", ".join([" ".join(c) for c in citation.creators])
              content = f"Creators: {creators_string}"
              doc = Document(content=content, meta=citation.dict())
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

def get_default_document_set_context_prompt(document_set: RagDocumentSet,
                                            include_all_relevant_meta: bool = False) -> str:
    if document_set == RagDocumentSet.VDI_DOCS:
        extended_meta = 'Price: {{ document.meta["price"] }}' if include_all_relevant_meta else ""
        return """Documents:
{% for document in documents %}""" + """
    Abstract: {{ document.meta["abstract"] }}
    Author: {{ document.meta["author"] }}
    Title: {{ document.meta["title"] }}
    Release date: {{ document.meta["release_date"] }}
    Currency: {{ document.meta["currency"] }}
    """ + extended_meta + """
{% endfor %}"""
    elif document_set == RagDocumentSet.SCIENCE_PAPERS:
        extended_meta = 'Creators: {{ document.meta["creators"] }}' if include_all_relevant_meta else ""
        return """Documents:
{% for document in documents %}""" + """
    Abstract: {{ document.meta["abstractNote"] }}
    Title: {{ document.meta["title"] }}
    Tags: {{ document.meta["tags"] }}
    Publication year: {{ document.meta["date"] }}
    Type: {{ document.meta["entry_type"] }}
    DOI: {{ document.meta["doi"] }}
    """ + extended_meta + """
{% endfor %}"""
    else:
        logging.warning(f"No system prompt defined for document_set {document_set}")
        return ""