SYSTEM_PROMPT = """
You are RAGnosis AI.

Rules:

1. Answer ONLY from provided context.
2. Never use outside knowledge.
3. If context is insufficient, say:

   "Insufficient evidence found in the manual."

4. Include citations.

5. Every claim must be grounded in context.

6. Do not hallucinate.

Answer format:

Diagnosis:
...

Solution:
...

Citations:
[Section | Page]
"""

def build_prompt(
    query: str,
    chunks: list
):

    context_parts = []

    for chunk in chunks:

        context_parts.append(
            f"""
SECTION:
{chunk["section"]}

PAGE:
{chunk["page"]}

CONTENT:
{chunk["text"]}
"""
        )

    context = "\n\n".join(
        context_parts
    )

    user_prompt = f"""
Question:

{query}

Context:

{context}
"""

    return SYSTEM_PROMPT, user_prompt