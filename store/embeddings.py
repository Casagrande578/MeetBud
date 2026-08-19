from __future__ import annotations

import ollama

MODEL = "embeddinggemma"


def _client(client: ollama.Client | None) -> ollama.Client:
    return client or ollama.Client()


def embed_query(text: str, client: ollama.Client | None = None) -> list[float]:
    """Embed a search query for retrieval against stored documents."""
    prefixed = f"task: search result | query: {text}"
    response = _client(client).embed(model=MODEL, input=prefixed)
    return response.embeddings[0]


def embed_documents(
    texts: list[str], titles: list[str | None] | None = None, client: ollama.Client | None = None
) -> list[list[float]]:
    """Batch-embed documents (e.g. note summaries) for storage."""
    titles = titles or [None] * len(texts)
    prefixed = [f"title: {title or 'none'} | text: {text}" for title, text in zip(titles, texts)]
    response = _client(client).embed(model=MODEL, input=prefixed)
    return response.embeddings


def embed_document(text: str, title: str | None = None, client: ollama.Client | None = None) -> list[float]:
    """Embed a single document. Prefer embed_documents when embedding many at once."""
    return embed_documents([text], [title], client=client)[0]
