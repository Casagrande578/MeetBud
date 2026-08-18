"""Extract structured knowledge from a Note via a local Ollama model.

Uses Ollama's structured-output mode (format=<json schema>) so the model is
constrained to valid JSON, then validates the result against ExtractedNote.
Failed attempts are retried and logged to data/failures.jsonl for inspection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import ollama
from pydantic import ValidationError

from extract.schema import ExtractedNote
from ingest.load_nodes import Note

MODEL = "qwen2.5:7b"
MAX_RETRIES = 2
FAILURES_LOG = Path("data/failures.jsonl")

_SYSTEM_PROMPT = (
    "You extract structured knowledge from meeting notes for a searchable "
    "knowledge base. Read the note below and produce a summary, action "
    "items, decisions, topics, and participants as JSON matching the given "
    "schema. Only use information present in the note — do not invent "
    "names, dates, or facts that aren't stated."
)


@dataclass
class ExtractionResult:
    note_id: str
    extracted: ExtractedNote | None
    attempts: int
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.extracted is not None


def _log_failure(note: Note, attempt: int, raw_response: str, error: str) -> None:
    FAILURES_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FAILURES_LOG.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "note_id": note.id,
                    "attempt": attempt,
                    "raw_response": raw_response,
                    "error": error,
                }
            )
            + "\n"
        )


def extract_note(note: Note, client: ollama.Client | None = None) -> ExtractionResult:
    """Extract structured knowledge from one note, retrying on validation failure."""
    client = client or ollama.Client()

    last_error = "unknown error"
    for attempt in range(1, MAX_RETRIES + 2):
        response = client.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": note.raw_text},
            ],
            format=ExtractedNote.model_json_schema(),
            options={"temperature": 0},
        )
        raw_content = response.message.content or ""
        try:
            extracted = ExtractedNote.model_validate_json(raw_content)
            return ExtractionResult(note_id=note.id, extracted=extracted, attempts=attempt)
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            _log_failure(note, attempt, raw_content, last_error)

    return ExtractionResult(note_id=note.id, extracted=None, attempts=MAX_RETRIES + 1, error=last_error)


def extract_notes(notes: list[Note], client: ollama.Client | None = None) -> list[ExtractionResult]:
    """Extract structured knowledge from every note, sequentially."""
    client = client or ollama.Client()
    return [extract_note(note, client=client) for note in notes]
