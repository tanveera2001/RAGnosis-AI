from __future__ import annotations

import re

from rag.config import (
    MIN_QUERY_LENGTH,
    RELEVANCE_THRESHOLD,
)


# ============================================================
# Prompt Injection Detection
# ============================================================

_INJECTION_PATTERNS = re.compile(
    r"""
    (
        ignore\s+(previous|all|above|prior)\s+instructions?
        |
        disregard\s+(previous|all|above|prior)\s+instructions?
        |
        forget\s+(the|your)\s+(previous|above|prior)
        |
        you\s+are\s+now
        |
        act\s+as
        |
        pretend\s+(you\s+are|to\s+be)
        |
        new\s+instructions?
        |
        system\s+prompt
        |
        reveal\s+(your|the)\s+(system\s+)?prompt
        |
        show\s+(me\s+)?your\s+(system\s+)?instructions?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ============================================================
# Query Validation
# ============================================================

def validate_query(
    query: str
) -> tuple[bool, str]:
    """
    Validate a user query before retrieval.

    Returns:
        (True, "") when the query is acceptable.

        (False, reason) when the query should be refused.
    """

    # --------------------------------------------------------
    # Check that query exists
    # --------------------------------------------------------

    if not isinstance(query, str):
        return (
            False,
            "Query must be a text string."
        )

    # --------------------------------------------------------
    # Remove leading/trailing whitespace
    # --------------------------------------------------------

    cleaned_query = query.strip()

    # --------------------------------------------------------
    # Empty query
    # --------------------------------------------------------

    if not cleaned_query:
        return (
            False,
            "Query is empty."
        )

    # --------------------------------------------------------
    # Very short query
    # --------------------------------------------------------

    if len(cleaned_query) < MIN_QUERY_LENGTH:
        return (
            False,
            "Query is too short to be a diagnostic question."
        )

    # --------------------------------------------------------
    # Prompt injection detection
    # --------------------------------------------------------

    if _INJECTION_PATTERNS.search(
        cleaned_query
    ):
        return (
            False,
            "Query contains a disallowed instruction pattern."
        )

    return True, ""


# ============================================================
# Retrieval Quality Policy
# ============================================================

def check_retrieval_quality(
    chunks: list[dict],
    distances: list[float],
    threshold: float = RELEVANCE_THRESHOLD,
) -> tuple[bool, str]:
    """
    Determine whether retrieval produced sufficient evidence.

    ChromaDB cosine distance:
        lower = more similar
        higher = less similar
    """

    # --------------------------------------------------------
    # No retrieved chunks
    # --------------------------------------------------------

    if not chunks:
        return (
            False,
            "No relevant manual sections were found."
        )

    # --------------------------------------------------------
    # No distances
    # --------------------------------------------------------

    if not distances:
        return (
            False,
            "Retrieved evidence has no relevance scores."
        )

    # --------------------------------------------------------
    # Validate threshold
    # --------------------------------------------------------

    if threshold < 0:
        return (
            False,
            "Invalid relevance threshold."
        )

    # --------------------------------------------------------
    # Find sufficiently relevant chunks
    # --------------------------------------------------------

    relevant_distances = [
        distance
        for distance in distances
        if distance <= threshold
    ]

    # --------------------------------------------------------
    # Reject if every result is weak
    # --------------------------------------------------------

    if not relevant_distances:
        return (
            False,
            "Retrieved sections are not sufficiently relevant "
            "to the question."
        )

    return True, ""


# ============================================================
# Citation Validation
# ============================================================

def enforce_citation_coverage(
    citations,
    chunks: list[dict]
) -> bool:
    """
    Verify that every returned citation refers to
    evidence that was actually retrieved.

    This prevents the system from citing a page that
    was never supplied to the LLM.
    """

    if not citations:
        return False

    retrieved_sources = set()

    for chunk in chunks:

        source = (
            chunk.get("manual"),
            chunk.get("section"),
            chunk.get("page"),
        )

        retrieved_sources.add(source)

    for citation in citations:

        source = (
            citation.manual,
            citation.section,
            citation.page,
        )

        if source not in retrieved_sources:
            return False

    return True


# ============================================================
# Deterministic Refusal
# ============================================================

def build_refusal(
    reason: str,
    model: str = "none"
) -> dict:
    """
    Create a deterministic refusal response.

    This response does not call the LLM.
    """

    return {
        "answer": (
            "I cannot answer this question from the "
            "available Dell Precision 5560 manuals. "
            f"Reason: {reason}"
        ),
        "citations": [],
        "insufficient_evidence": True,
        "model": model,
    }