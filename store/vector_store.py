from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb

from extract.schema import ExtractedNote
from ingest.load_nodes import Note

DB_PATH = "data/chroma"
COLLECTION_NAME = "notes"


@dataclass
class SearchResult:
    note_id: str
    title: str
    date: str | None
    summary: str
    similarity: float


def get_collection(path: str | Path = DB_PATH) -> chromadb.api.models.Collection.Collection:
    client = chromadb.PersistentClient(path=str(path))
    # cosine space so query() distances translate directly to similarity scores
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def add_note(collection, note: Note, extracted: ExtractedNote, embedding: list[float]) -> None:
    """Store one note's summary embedding + metadata. Upserts, so re-ingesting is safe."""
    collection.upsert(
        ids=[note.id],
        embeddings=[embedding],
        documents=[extracted.summary],
        metadatas=[
            {
                "title": note.title,
                "date": note.date or "",
                "participants": ", ".join(extracted.participants),
                "topics": ", ".join(extracted.topics),
            }
        ],
    )


def query(collection, query_embedding: list[float], top_k: int = 5) -> list[SearchResult]:
    """Semantic search: return the top_k most similar notes with similarity scores."""
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    if not results["ids"][0]:
        return []

    return [
        SearchResult(
            note_id=note_id,
            title=metadata.get("title", ""),
            date=metadata.get("date") or None,
            summary=document,
            similarity=1 - distance,  # cosine space: distance = 1 - cosine similarity
        )
        for note_id, metadata, document, distance in zip(
            results["ids"][0], results["metadatas"][0], results["documents"][0], results["distances"][0]
        )
    ]
