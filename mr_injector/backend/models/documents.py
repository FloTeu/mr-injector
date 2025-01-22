import logging
from enum import StrEnum, auto
from pathlib import Path

from pydantic import BaseModel
from datetime import date

import mr_injector


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


class RagDocumentSet(StrEnum):
  VDI_DOCS = auto()
  SCIENCE_PAPERS = auto()

  @classmethod
  def is_file(cls, doc_set):
    """Returns True if RagDocumentSet is a single file"""
    if doc_set == cls.SCIENCE_PAPERS:
      return True
    else:
      return False

  @classmethod
  def to_list(cls):
    document_sets = []
    # return only available data sets
    for doc_set in list(map(lambda c: c.value, cls)):
      file_suffix = ".json" if cls.is_file(cls(doc_set)) else ""
      if (Path(mr_injector.__path__[0]).parent / f"files/{doc_set}{file_suffix}").exists():
        document_sets.append(doc_set)
      else:
        logging.warning(f"Could not find document set {doc_set}")
    return document_sets

  def get_path(self) -> Path:
    file_suffix = ".json" if self.is_file(self) else ""
    return Path(mr_injector.__path__[0]).parent / f"files/{self.value}{file_suffix}"
