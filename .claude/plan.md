# Local Knowledge Pipeline — Build Plan

## Goal
Build a fully local (no external API calls) pipeline that ingests meeting notes/transcripts,
extracts structured knowledge with a local LLM, stores it in a vector DB, and answers queries
through an orchestrator/agent that picks the right retrieval strategy. Ship with an eval suite
that produces measurable numbers (retrieval accuracy, latency) — this is the artifact used to
answer "show me something verifiable" in job applications.

## Hardware target
- RTX 4060 Ti 8GB VRAM, Ryzen 9900X, running Ollama.
- Models: `qwen2.5:7b` (extraction + agent), `embeddinggemma` (embeddings, via Ollama).
- Keep total resident VRAM under ~7GB so extraction model + embedding model can stay loaded together.

## Tech stack
- Python 3.11+
- `ollama` (local model serving) — pull `qwen2.5:7b` and `embeddinggemma`
- `chromadb` (vector store, local, zero infra)
- `pydantic` (structured output validation)
- `typer` or plain `argparse` (CLI)
- `pytest` (eval harness)
- Optional later: `faster-whisper` (audio transcription), `streamlit` (UI)

## Repo structure
```
knowledge-pipeline/
  ingest/
    __init__.py
    load_notes.py        # loads .md/.txt files from data/samples into normalized Note objects
  extract/
    __init__.py
    schema.py             # pydantic models: ExtractedNote (summary, action_items, decisions, topics, participants)
    extractor.py           # calls Ollama qwen2.5:7b with JSON-mode prompt, validates against schema, retries on failure
  store/
    __init__.py
    embeddings.py          # wraps embeddinggemma calls with correct instruct-prefix formatting
    vector_store.py        # Chroma client: add(note), query(text, filters)
  agent/
    __init__.py
    tools.py               # semantic_search, filter_by_metadata, get_timeline — plain functions
    orchestrator.py         # router: LLM picks a tool given the query, executes, returns answer + sources
  eval/
    __init__.py
    queries.py              # 15-20 hand-written test queries with expected source note IDs
    run_eval.py              # computes precision@k, tool-selection correctness, latency; prints report
  data/
    samples/                 # sample/synthetic meeting notes (.md), generated if none provided
  cli.py                      # single entrypoint: `python cli.py ingest|ask|eval`
  requirements.txt
  README.md                   # architecture diagram description + design tradeoffs + eval results
  .env.example
```

## Phase 0 — Environment setup
- [ ] Install Ollama, confirm `ollama --version`
- [ ] `ollama pull qwen2.5:7b`
- [ ] `ollama pull embeddinggemma`
- [ ] Create Python venv, `pip install ollama chromadb pydantic typer pytest`
- [ ] Scaffold the repo structure above with empty modules
- [ ] Sanity check: script that sends one prompt to qwen2.5:7b via Ollama Python client and prints the response
- **Checkpoint:** repo exists, both models respond to a basic call.

## Phase 1 — Ingestion
- [ ] `ingest/load_notes.py`: read all `.md`/`.txt` files from `data/samples/`, parse into a `Note`
      dataclass: `{id, date, title, raw_text, source_path}`
- [ ] If `data/samples/` is empty, generate 15-20 synthetic meeting notes via qwen2.5:7b covering a
      few recurring topics (pricing, roadmap, hiring, incidents) across several fake dates/participants,
      so retrieval and multi-hop queries have something real to find
- [ ] Unit test: loader returns the right count and required fields are non-empty
- **Checkpoint:** `python cli.py ingest --dry-run` prints normalized notes to stdout.

## Phase 2 — Extraction
- [x] `extract/schema.py`: pydantic `ExtractedNote` — `summary: str`, `action_items: list[str]`,
      `decisions: list[str]`, `topics: list[str]`, `participants: list[str]`
- [x] `extract/extractor.py`: prompt qwen2.5:7b via Ollama structured output (`format=<json schema>`),
      parse into `ExtractedNote`, retry up to 2x on validation failure, log failures to `data/failures.jsonl`
- [ ] Save `ExtractedNote` objects alongside raw notes (currently only printed to stdout — persistence
      lands with Phase 3 storage)
- [x] **Checkpoint:** `python cli.py ingest` produces clean structured JSON for every sample note;
      report failure rate in stdout. Verified: 8/8 notes extracted, 0 failures, 1 attempt each.

## Phase 3 — Storage / RAG
- [ ] `store/embeddings.py`: wrap embeddinggemma calls — MUST use the instruct-prefixed format
      (`"task: search result | query: ..."` style, per model card) for queries vs. documents;
      write a 3-line sanity test comparing cosine similarity of a known matching pair vs. a
      known non-matching pair before trusting the pipeline
- [ ] `store/vector_store.py`: Chroma collection, `add(note_id, embedding, text, metadata)`,
      `query(text, top_k, metadata_filter=None)`; metadata = `{date, participants, topics}`
- [ ] Embed and store every extracted note (embed the `summary`, not raw transcript, for retrieval
      quality; keep raw text retrievable by id for display)
- **Checkpoint:** `python cli.py ask "<query>"` (semantic-search-only, no agent yet) returns
      top-k relevant notes with similarity scores.

## Phase 4 — Orchestrator / Agent
- [ ] `agent/tools.py`: three plain Python functions —
      `semantic_search(query, top_k)`, `filter_by_metadata(participant=None, date_range=None, topic=None)`,
      `get_timeline(topic)` (returns all notes mentioning a topic sorted by date, for "has X changed" queries)
- [ ] `agent/orchestrator.py`: give qwen2.5:7b tool definitions (Ollama function-calling / tool-use
      format), let it pick and call one or more tools, then synthesize a final answer citing note ids/dates
- [ ] CLI prints which tool(s) were selected + the reasoning, then the answer with sources
- **Checkpoint:** `python cli.py ask "<query>"` now runs through the full agent, shows tool choice,
      returns cited answer.

## Phase 5 — Eval (this is the deliverable)
- [ ] `eval/queries.py`: 15-20 queries spanning all three retrieval strategies, each with the
      expected correct source note id(s) and expected tool choice
- [ ] `eval/run_eval.py`: runs every query through the orchestrator, computes:
      - retrieval precision@k against expected sources
      - tool-selection accuracy (did it pick the right strategy)
      - average end-to-end latency (extraction batch + per-query agent latency, separately)
- [ ] Print a clean report table; save to `eval/results.md`
- **Checkpoint:** `python cli.py eval` outputs a report with concrete numbers — this is what goes
      in the interview answer.

## Phase 6 — Optional polish (only if time remains)
- [ ] `faster-whisper` audio ingestion path feeding into the same `Note` format as Phase 1
- [ ] Streamlit UI: text box for queries, shows tool choice + sources + answer
- [ ] Try `qwen2.5:14b` for the agent step only, re-run eval, add a comparison table to README
      (accuracy vs. latency tradeoff — good interview talking point)
- [ ] README.md: architecture diagram (ASCII or Mermaid), why each model/library was chosen,
      eval results table, known limitations

## Definition of done
- `python cli.py ingest`, `python cli.py ask "..."`, and `python cli.py eval` all work end-to-end
  with zero external API calls
- `eval/results.md` has concrete precision/accuracy/latency numbers
- README documents the architecture and design tradeoffs clearly enough to talk through in an interview
