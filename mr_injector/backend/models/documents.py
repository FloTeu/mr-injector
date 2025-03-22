import hashlib
import logging
from enum import StrEnum, auto
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator
from datetime import date

import mr_injector
from mr_injector.backend.utils import hash_text


class Document(BaseModel):
    content: str = Field(description="Embedding input text")
    meta: dict[str, Any]
    id: str | None = None


    def __hash__(self):
        return hash(self.content)

    def __eq__(self, other):
        return self.content == other.content

    @model_validator(mode='after')
    def ensure_id(self) -> Self:
        if self.id is None:
            self.id = hash_text(self.content)
        return self


class VDIDoc(BaseModel):
  """Defines a single 'VDI Richtlinie'"""
  title: str
  title_en: str
  abstract: str
  release_date: date
  publisher: str
  author: str | None
  languages: list[str] | None
  pages: int | None
  manuals: list[str]
  price: float | None
  currency: str = "€"


class SciencePaper(BaseModel):
  """Defines a single citation"""
  title: str
  creators: list[list[str]]
  tags: list[str]
  date: date
  abstract: str | None
  entry_type: str
  doi: str | None


class ResumeDataSet(BaseModel):
  """Defines a single citation"""
  Category: str
  Resume: str
  Name: str

class RagDocumentSet(StrEnum):
  VDI_DOCS = auto()
  SCIENCE_PAPERS = auto()
  RESUMES = auto()

  @classmethod
  def is_file(cls, doc_set):
    """Returns True if RagDocumentSet is a single file"""
    if doc_set == cls.SCIENCE_PAPERS:
      return True
    elif doc_set == cls.RESUMES:
      return True
    else:
      return False

  @classmethod
  def get_file_suffix(cls, doc_set):
    """Returns True if RagDocumentSet is a single file"""
    if doc_set == cls.SCIENCE_PAPERS:
      return ".json"
    elif doc_set == cls.RESUMES:
      return ".csv"
    else:
      return ".json"

  @classmethod
  def to_list(cls):
    document_sets = []
    # return only available data sets
    for doc_set in list(map(lambda c: c.value, cls)):
      file_suffix = cls.get_file_suffix(cls(doc_set)) if cls.is_file(cls(doc_set)) else ""
      if (Path(mr_injector.__path__[0]).parent / f"files/{doc_set}{file_suffix}").exists():
        document_sets.append(doc_set)
      else:
        logging.warning(f"Could not find document set {doc_set}")
    return document_sets

  def get_path(self) -> Path:
    file_suffix = self.get_file_suffix(self) if self.is_file(self) else ""
    return Path(mr_injector.__path__[0]).parent / f"files/{self.value}{file_suffix}"

