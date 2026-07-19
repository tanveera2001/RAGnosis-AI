import json

from tqdm import tqdm

from rag.config import PROCESSED_DIR

from rag.embeddings import embed_batch

from rag.vectorstore import VectorStore


CHUNK_FILE = PROCESSED_DIR / "chunks.jsonl"


def load_chunks():

    chunks = []

    with open(
        CHUNK_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            chunks.append(
                json.loads(line)
            )

    return chunks


def build_index():

    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks")

    store = VectorStore()

    store.reset()

    BATCH_SIZE = 32

    for i in tqdm(
        range(0, len(chunks), BATCH_SIZE)
    ):

        batch = chunks[i:i+BATCH_SIZE]

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        embeddings = embed_batch(texts)

        ids = [
            f"{chunk['manual']}_p{chunk['page']}_{i+j}"
            for j, chunk in enumerate(batch)
        ]

        metadatas = []

        for chunk in batch:

            metadatas.append({
                "page": chunk["page"],
                "section": chunk["section"]
            })

        store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    print(
        f"Indexed {store.count()} chunks"
    )


if __name__ == "__main__":
    build_index()