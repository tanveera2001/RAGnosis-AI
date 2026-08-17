
from dataclasses import dataclass

from rag.prompt import build_prompt
from rag.config import (
    OPENROUTER_MODEL,
    RELEVANCE_THRESHOLD,
)

from agent import policy


@dataclass
class AgentResponse:
    answer: str
    citations: list
    insufficient_evidence: bool
    model: str


class DiagnosticAgent:

    def __init__(
        self,
        retriever,
        answerer,
        top_k: int = 5,
    ):
        self.retriever = retriever
        self.answerer = answerer
        self.top_k = top_k

    def run(
        self,
        query: str,
    ) -> AgentResponse:

        # ====================================================
        # STEP 1 — Validate user input
        # ====================================================

        valid, reason = policy.validate_query(
            query
        )

        if not valid:

            refusal = policy.build_refusal(
                reason=reason
            )

            return AgentResponse(
                answer=refusal["answer"],
                citations=[],
                insufficient_evidence=True,
                model=refusal["model"],
            )

        # Normalize the query
        query = query.strip()

        # ====================================================
        # STEP 2 — Retrieve evidence
        # ====================================================

        scored_chunks = (
            self.retriever.retrieve_with_scores(
                query=query,
                top_k=self.top_k,
            )
        )

        # Separate chunks and distances
        chunks = [
            item[0]
            for item in scored_chunks
        ]

        distances = [
            item[1]
            for item in scored_chunks
        ]

        # ====================================================
        # STEP 3 — Retrieval quality guardrail
        # ====================================================

        sufficient, reason = (
            policy.check_retrieval_quality(
                chunks=chunks,
                distances=distances,
                threshold=RELEVANCE_THRESHOLD,
            )
        )

        if not sufficient:

            refusal = policy.build_refusal(
                reason=reason
            )

            return AgentResponse(
                answer=refusal["answer"],
                citations=[],
                insufficient_evidence=True,
                model=refusal["model"],
            )

        # ====================================================
        # STEP 4 — Build grounded prompt
        # ====================================================

        system_prompt, user_prompt = build_prompt(
            query=query,
            chunks=chunks,
        )

        # ====================================================
        # STEP 5 — Generate answer
        # ====================================================

        answer = self.answerer.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # ====================================================
        # STEP 6 — Extract citations from generated answer
        # ====================================================

        citations = self.answerer.extract_citations(
            answer
        )

        # ====================================================
        # STEP 7 — Citation guardrail
        # ====================================================

        citation_valid = (
            policy.enforce_citation_coverage(
                citations=citations,
                chunks=chunks,
            )
        )

        if not citation_valid:

            refusal = policy.build_refusal(
                reason=(
                    "The generated answer could not be "
                    "verified against the retrieved evidence."
                )
            )

            return AgentResponse(
                answer=refusal["answer"],
                citations=[],
                insufficient_evidence=True,
                model=refusal["model"],
            )

        # ====================================================
        # STEP 8 — Return safe result
        # ====================================================

        return AgentResponse(
            answer=answer,
            citations=citations,
            insufficient_evidence=False,
            model=OPENROUTER_MODEL,
        )
