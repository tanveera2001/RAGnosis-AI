from rag.embeddings import embed_text
from rag.vectorstore import VectorStore


class Retriever:

    def __init__(
        self,
        store: VectorStore,
        top_k: int = 5
    ):
        self.store = store
        self.top_k = top_k

    def retrieve(
        self,
        query: str
    ):
        query_embedding = embed_text(query)

        results = self.store.search(
            query_embedding=query_embedding,
            top_k=self.top_k
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        chunks = []

        for doc, meta in zip(documents, metadatas):
            chunks.append({
                "text": doc,
                "manual": meta.get("manual", "Unknown"),
                "page": meta.get("page"),
                "section": meta.get("section"),
            })

        print("\nRetrieved chunk:")
        print(chunks[0])

        return chunks