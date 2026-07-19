from rag.embeddings import embed_text
from rag.vectorstore import VectorStore

query = "battery removal"

print(f"\nQuery: {query}\n")

store = VectorStore()

embedding = embed_text(query)

results = store.search(
    embedding,
    top_k=3
)

docs = results["documents"][0]
metas = results["metadatas"][0]

for i, (doc, meta) in enumerate(
    zip(docs, metas),
    start=1
):
    print(f"Top Result #{i}")

    print(
        f"Section: {meta['section']}"
    )

    print(
        f"Page: {meta['page']}"
    )

    print()

    print(doc[:300])

    print("\n" + "=" * 80 + "\n")