from dataclasses import dataclass

from rag.prompt import build_prompt
from rag.config import OPENROUTER_MODEL


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

        query = query.strip()

        if not query:
            return AgentResponse(
                answer="Please enter a question.",
                citations=[],
                insufficient_evidence=True,
                model=OPENROUTER_MODEL,
            )

        chunks = self.retriever.retrieve(query)

        if not chunks:
            return AgentResponse(
                answer="Insufficient evidence found in the manual.",
                citations=[],
                insufficient_evidence=True,
                model=OPENROUTER_MODEL,
            )

        system_prompt, user_prompt = build_prompt(
            query=query,
            chunks=chunks,
        )

        answer = self.answerer.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        citations = self.answerer.extract_citations(
            chunks
        )

        return AgentResponse(
            answer=answer,
            citations=citations,
            insufficient_evidence=False,
            model=OPENROUTER_MODEL,
        )