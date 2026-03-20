from pydantic import BaseModel, Field
from typing import Literal


class ClassifierOutput(BaseModel):
    criterion_1: bool
    criterion_2: bool
    criterion_3: bool
    criterion_4: bool
    criterion_5: bool
    criterion_6: bool
    criterion_7: bool
    classification: Literal["A1", "A2", "A3"]


class SummarizerOutput(BaseModel):
    title: str = Field(min_length=1)
    apa7_citation: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    scoring_basis: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    method: str = Field(min_length=1)
    research_model: str = Field(min_length=1)
    findings: str = Field(min_length=1)
    contribution: str = Field(min_length=1)
    limitations: str = Field(min_length=1)
