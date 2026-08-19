from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedNote(BaseModel):
    summary: str = Field(description="2-3 sentence summary of what the meeting covered.")
    action_items: list[str] = Field(default_factory=list, description="Concrete follow-up tasks, one per item.")
    decisions: list[str] = Field(default_factory=list, description="Decisions the group committed to.")
    topics: list[str] = Field(default_factory=list, description="Short topic tags, e.g. 'pricing', 'hiring'.")
    participants: list[str] = Field(default_factory=list, description="Names of people present or mentioned.")
