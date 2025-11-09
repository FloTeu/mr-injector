import logging
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from mr_injector.backend.models.documents import VDIDoc, SciencePaper, RagDocumentSet, Document, ResumeDataSet
from mr_injector.backend.utils import get_random_name


def extract_resume_documents(file_path: Path, drop_duplicates: bool = True) -> List[Document]:
    assert file_path.exists(), f"file {file_path} does not exist"
    assert "csv" == file_path.name.split(".")[-1], "must be a .csv file"
    resume_df = pd.read_csv(file_path)
    docs = []
    for i, df_row in resume_df.iterrows():
        content = df_row["Category"] + " " + df_row["Resume"]
        random_name = get_random_name()
        resume = ResumeDataSet(**{**df_row.to_dict(), "Name": random_name})
        docs.append(Document(
            content=content,
            meta=resume.model_dump(),
            id=str(i)
        ))

    if drop_duplicates:
        docs = list(set(docs))

    return docs


def create_vdi_documents(directory_path: Path | str) -> List[Document]:
    """
    Iterates over all JSON files in the specified directory and creates a list of Documents.

    Args:
    directory_path (str): The path to the directory containing JSON files.

    Returns:
    List[Document]: A list of Document objects.
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
                    doc = Document(
                        content=vdi_doc.abstract,
                        meta={k: ", ".join(v) if isinstance(v, list) else v for k, v in vdi_doc.model_dump(mode='json').items()},
                        id=str(i)
                    )
                    documents.append(doc)
            except Exception as e:
                print(f"Could not load json file {i} {filename}", str(e))
    return documents


def create_bibtex_citation_documents(file_path: Path | str) -> List[Document]:
    """
    Iterates over all entries in a bibtex file and creates a list of Documents.

    Args:
    file_path (str): The path to the reference file in bibtex format.

    Returns:
    List[Document]: A list of Document objects.
    """
    documents = []
    year_pattern = re.compile(r"[0-9][0-9][0-9][0-9]")
    with open(file_path, 'r', encoding='utf-8') as file:
      json_content = json.load(file)
      doc_id = 0
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
          creators_string = ", ".join([" ".join(c) for c in citation.creators])
          meta={k: ", ".join(v) if isinstance(v, list) else v for k, v in citation.model_dump(mode='json').items() if k != "creators"}
          if len(citation.creators) > 0:
              meta["creators"] = creators_string
          doc = Document(
              content=content,
              meta=meta,
              id=str(doc_id)
          )
          documents.append(doc)
          doc_id += 1

          if len(citation.creators) > 0:
              content = f"Creators: {creators_string}"
              doc = Document(
                  content=content,
                  meta=meta,
                  id=str(doc_id)
              )
              documents.append(doc)
              doc_id += 1

    return documents


def chromadb_results_to_documents(results: dict) -> List[Document]:
    """
    Convert ChromaDB query results to Document objects.

    Args:
        results: ChromaDB query results with 'documents', 'metadatas', 'ids'

    Returns:
        List[Document]: List of Document objects
    """
    documents = []
    if results['documents'] and len(results['documents']) > 0:
        # ChromaDB returns nested lists, flatten them
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        ids = results['ids'][0]

        for content, meta, doc_id in zip(docs, metas, ids):
            documents.append(Document(
                content=content,
                meta=meta,
                id=doc_id
            ))

    return documents


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
    Abstract: {{ document.meta["abstract"] }}
    Title: {{ document.meta["title"] }}
    Tags: {{ document.meta["tags"] }}
    Publication year: {{ document.meta["date"] }}
    Type: {{ document.meta["entry_type"] }}
    """ + extended_meta + """
{% endfor %}"""
    else:
        raise ValueError(f"Unknown document set: {document_set}")
