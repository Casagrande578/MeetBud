"""Single entrypoint: python cli.py ingest|ask|eval"""

from __future__ import annotations

import typer

from ingest.load_nodes import load_notes

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

    # Extraction (Phase 2) and storage (Phase 3) land here once those modules exist.
    typer.echo(f"Loaded {len(notes)} notes. Extraction/storage not implemented yet.")


@app.command()
def ask(query: str) -> None:
    """Answer a query by routing through the retrieval agent."""
    typer.echo("ask is not implemented yet (Phase 3/4).")
    raise typer.Exit(code=1)


@app.command(name="eval")
def eval_cmd() -> None:
    """Run the eval suite and print a report."""
    typer.echo("eval is not implemented yet (Phase 5).")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
