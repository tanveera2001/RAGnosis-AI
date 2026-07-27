from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.agent import DiagnosticAgent
from rag.answerer import Answerer
from rag.retriever import Retriever
from rag.vectorstore import VectorStore

from rag.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    TOP_K,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize all RAG components once when FastAPI starts.
    """

    store = VectorStore()

    retriever = Retriever(
        store=store,
        top_k=TOP_K,
    )

    answerer = Answerer()

    agent = DiagnosticAgent(
        retriever=retriever,
        answerer=answerer,
        top_k=TOP_K,
    )

    app.state.store = store
    app.state.agent = agent

    yield


app = FastAPI(
    title="RAGnosis AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    top_k: int = TOP_K


class CitationOut(BaseModel):
    manual: str
    section: str
    page: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    insufficient_evidence: bool
    model: str


@app.get("/")
def root():
    return {
        "message": "Welcome to RAGnosis AI"
    }


@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(req: ChatRequest):
    """
    Main RAG endpoint.
    """

    agent: DiagnosticAgent = app.state.agent

    result = agent.run(req.query)

    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationOut(
                manual=c.manual,
                section=c.section,
                page=c.page,
            )
            for c in result.citations
        ],
        insufficient_evidence=result.insufficient_evidence,
        model=result.model,
    )


@app.get("/health")
def health():
    """
    Health endpoint.
    """

    store: VectorStore = app.state.store

    try:
        count = store.count()
    except Exception:
        count = -1

    return {
        "status": "ok",
        "chunks_indexed": count,
        "embed_model": EMBEDDING_MODEL,
        "collection": COLLECTION_NAME,
    }