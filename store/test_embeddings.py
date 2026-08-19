"""Sanity check: a matching query/document pair must score higher than a non-matching one."""

from store.embeddings import embed_documents, embed_query


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = sum(x * x for x in a) ** 0.5 * sum(y * y for y in b) ** 0.5
    return dot / norm


def test_matching_pair_scores_higher_than_non_matching():
    query = embed_query("what did we decide about pricing tiers?")
    docs = embed_documents(
        ["We froze pricing for Q1 and will draft a usage-based add-on proposal."],
        ["Pricing Strategy Kickoff"],
    ) + embed_documents(
        ["The reindexing job leaked memory and caused a 47-minute search outage."],
        ["Incident Postmortem"],
    )
    matching, non_matching = _cosine(query, docs[0]), _cosine(query, docs[1])
    assert matching > non_matching
