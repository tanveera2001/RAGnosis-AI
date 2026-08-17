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
        query: str,
        top_k: int | None = None
    ):
        """
        Retrieve the most relevant chunks without exposing
        the underlying ChromaDB response structure.
        """

        k = top_k if top_k is not None else self.top_k

        query_embedding = embed_text(query)

        results = self.store.search(
            query_embedding=query_embedding,
            top_k=k
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        chunks = []

        for index, (doc, meta) in enumerate(
            zip(documents, metadatas)
        ):

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            chunks.append(
                {
                    "text": doc,
                    "manual": meta.get(
                        "manual",
                        "Unknown"
                    ),
                    "page": meta.get(
                        "page"
                    ),
                    "section": meta.get(
                        "section"
                    ),
                    "id": meta.get(
                        "id"
                    ),
                    "distance": distance,
                }
            )

        return chunks

    def retrieve_with_scores(
        self,
        query: str,
        top_k: int | None = None
    ):
        """
        Retrieve chunks together with their
        similarity distances.

        Returns:
            list[tuple[dict, float]]
        """

        chunks = self.retrieve(
            query=query,
            top_k=top_k
        )

        results = []

        for chunk in chunks:

            distance = chunk.get(
                "distance"
            )

            if distance is None:
                distance = 1.0

            results.append(
                (
                    chunk,
                    float(distance)
                )
            )

        return results