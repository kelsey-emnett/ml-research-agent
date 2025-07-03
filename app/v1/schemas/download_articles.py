from pydantic import BaseModel, Field
from app.v1.utils.constants import CROSSREF_FILTER
from typing import List, Optional


class CrossRefParams(BaseModel):
    query: str
    filter: str = Field(default=CROSSREF_FILTER)
    rows: int = 10


class Article(BaseModel):
    doi: str = Field(alias="DOI")
    title: List[str] = Field(alias="title")  # From context it seems title is a list
    author: List[dict] = Field(alias="author")  # Author appears to be a list of dicts
    year_published: int = Field(alias="published.date-parts.0.0")
    url: str = Field(alias="URL")
    abstract: Optional[str] = Field(None, alias="abstract")

    # Optional fields that might be added later
    file_name: Optional[str] = None
    output_path: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
