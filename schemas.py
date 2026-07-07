"""Structured output schemas for Form Sahayak agents.

Using output_schema (instead of free-form text) keeps state clean as it
passes between agents in the pipeline -- each downstream agent reads a
typed field from session state instead of having to parse prose.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DocumentClassification(BaseModel):
    doc_type: str = Field(
        description="Type of document, e.g. 'subsidy application', "
                    "'bank KYC form', 'court notice'"
    )
    risk_level: str = Field(
        description="'low', 'medium', or 'high'. Use 'high' for anything "
                    "involving eviction, court summons, deportation, or "
                    "other matters with serious legal consequences and a "
                    "hard deadline -- cases where a person should talk to "
                    "a professional, not just fill out a form with our help."
    )
    deadline_mentioned: Optional[str] = Field(
        default=None, description="Any deadline found in the document, in plain terms"
    )


class PlainLanguageSummary(BaseModel):
    what_it_is: str
    why_you_got_it: str
    what_you_need_to_do: str
    deadline: Optional[str] = None
    what_happens_if_ignored: Optional[str] = None
    unclear_parts: Optional[str] = Field(
        default=None,
        description="Anything genuinely ambiguous in the source document -- "
                    "do not guess, flag it here instead",
    )
