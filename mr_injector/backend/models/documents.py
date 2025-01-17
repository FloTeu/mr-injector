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


class RagDocumentSet(StrEnum):
  VDI_DOCS = auto()
  SCIENCE_PAPERS = auto()

  @classmethod
  def to_list(cls):
    document_sets = []
    # return only available data sets
    for doc_set in list(map(lambda c: c.value, cls)):
      if (Path(mr_injector.__path__[0]).parent / f"files/{doc_set}").exists():
        document_sets.append(doc_set)
      else:
        logging.warning(f"Could not find document set {doc_set}")
    return document_sets

  def get_path(self) -> Path:
    return Path(mr_injector.__path__[0]).parent / f"files/{self.value}"
