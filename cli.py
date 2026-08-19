from __future__ import annotations

import typer

from extract.extractor import extract_notes
from ingest.load_nodes import load_notes
from store.embeddings import embed_documents, embed_query
from store.vector_store import add_note, get_collection, query as query_store

app = typer.Typer(add_completion=False)

SAMPLES_DIR = "data/samples"


@app.command()
def ingest(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Load and print normalized notes without extracting/storing."
    ),
) -> None:
    """Load notes from data/samples, extract structured knowledge, and store them."""
    notes = load_notes(SAMPLES_DIR)

    if not notes:
        typer.echo(f"No .md/.txt notes found in {SAMPLES_DIR}/")
        raise typer.Exit(code=1)

    if dry_run:
        for note in notes:
            typer.echo(f"[{note.id}] {note.date or 'no-date'} — {note.title}")
            typer.echo(f"    source: {note.source_path}  ({len(note.raw_text)} chars)")
        typer.echo(f"\n{len(notes)} notes loaded.")
        return

    typer.echo(f"Loaded {len(notes)} notes. Extracting...")
    results = extract_notes(notes)

    failures = [r for r in results if not r.ok]
    ok_notes = [note for note, r in zip(notes, results) if r.ok]
    ok_results = [r for r in results if r.ok]

    for r in results:
        if r.ok:
            typer.echo(f"[{r.note_id}] ok ({r.attempts} attempt(s))")
            typer.echo(f"    {r.extracted.model_dump_json()}")
        else:
            typer.echo(f"[{r.note_id}] FAILED after {r.attempts} attempt(s): {r.error}")

    if ok_results:
        # embed the summary, not the raw transcript, for retrieval quality
        embeddings = embed_documents(
            [r.extracted.summary for r in ok_results], [note.title for note in ok_notes]
        )
        collection = get_collection()
        for note, r, embedding in zip(ok_notes, ok_results, embeddings):
            add_note(collection, note, r.extracted, embedding)

    typer.echo(
        f"\n{len(ok_results)}/{len(results)} notes extracted and stored "
        f"({len(failures)} failure(s))."
    )


@app.command()
def ask(
    query: str,
    top_k: int = typer.Option(5, "--top-k", help="Number of results to return."),
) -> None:
    """Semantic search over stored notes. (Agent routing lands in Phase 4.)"""
    collection = get_collection()
    if collection.count() == 0:
        typer.echo("No notes stored yet — run `python cli.py ingest` first.")
        raise typer.Exit(code=1)

    embedding = embed_query(query)
    results = query_store(collection, embedding, top_k=top_k)

    for r in results:
        typer.echo(f"[{r.note_id}] {r.date or 'no-date'} — {r.title}  (similarity: {r.similarity:.3f})")
        typer.echo(f"    {r.summary}")


@app.command(name="eval")
def eval_cmd() -> None:
    """Run the eval suite and print a report."""
    typer.echo("eval is not implemented yet (Phase 5).")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
