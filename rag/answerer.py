from dataclasses import dataclass
import re

from openai import OpenAI

from rag.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    TEMPERATURE,
)


# ============================================================
# Citation Model
# ============================================================

@dataclass
class Citation:
    manual: str
    section: str
    page: int


# ============================================================
# Citation Pattern
# ============================================================

_CITATION_PATTERN = re.compile(
    r"""
    \[
        Manual:\s*(.+?),
        \s*Section:\s*(.+?),
        \s*Page:\s*(\d+)
    \]
    """,
    re.IGNORECASE | re.VERBOSE,
)


class Answerer:

    def __init__(self):

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )

    # ========================================================
    # Generate Answer
    # ========================================================

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=OPENROUTER_MODEL,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return (
            response.choices[0]
            .message.content
            or ""
        )

    # ========================================================
    # Extract Actual LLM Citations
    # ========================================================

    def extract_citations(
        self,
        answer: str,
    ) -> list[Citation]:

        citations = []

        seen = set()

        matches = _CITATION_PATTERN.finditer(
            answer
        )

        for match in matches:

            manual = match.group(1).strip()

            section = match.group(2).strip()

            page = int(
                match.group(3)
            )

            key = (
                manual,
                section,
                page,
            )

            if key in seen:
                continue

            seen.add(key)

            citations.append(
                Citation(
                    manual=manual,
                    section=section,
                    page=page,
                )
            )

        return citations