import chromadb

from rag.config import (
    CHROMA_DIR,
    COLLECTION_NAME
)


class VectorStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR)
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            }
        )

    def add_documents(
        self,
        ids,
        embeddings,
        documents,
        metadatas
    ):

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def count(self):

        return self.collection.count()

    def search(
        self,
        query_embedding,
        top_k=5
    ):

        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

    def reset(self):

        try:
            self.client.delete_collection(
                COLLECTION_NAME
            )
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine"
            }
        )