from dataclasses import dataclass

from openai import OpenAI

from rag.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    TEMPERATURE,
)


@dataclass
class Citation:
    manual: str
    section: str
    page: int


class Answerer:

    def __init__(self):

        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )

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

        return response.choices[0].message.content

    def extract_citations(
        self,
        chunks: list[dict],
    ) -> list[Citation]:

        citations = []
        seen = set()

        for chunk in chunks:

            key = (
                chunk.get("manual"),
                chunk.get("section"),
                chunk.get("page"),
            )

            if key in seen:
                continue

            seen.add(key)

            citations.append(
                Citation(
                    manual=chunk.get("manual", "Unknown"),
                    section=chunk.get("section", "Unknown"),
                    page=int(chunk.get("page", 0)),
                )
            )

        return citations