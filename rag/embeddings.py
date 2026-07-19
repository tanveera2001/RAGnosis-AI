from sentence_transformers import SentenceTransformer

from rag.config import EMBEDDING_MODEL


_model = None


def get_embedding_model():
    """
    Singleton pattern.
    Loads model once.
    """

    global _model

    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")

        _model = SentenceTransformer(
            EMBEDDING_MODEL
        )

    return _model


def embed_text(text: str):
    """
    Convert text into embedding vector.
    """

    model = get_embedding_model()

    return model.encode(
        text,
        normalize_embeddings=True
    ).tolist()


def embed_batch(texts: list[str]):
    """
    Embed multiple texts.
    """

    model = get_embedding_model()

    return model.encode(
        texts,
        normalize_embeddings=True
    ).tolist()