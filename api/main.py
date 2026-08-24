from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent.agent import DiagnosticAgent
from rag.answerer import Answerer
from rag.config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    OPENROUTER_MODEL,
    TOP_K,
)
from rag.retriever import Retriever
from rag.vectorstore import VectorStore


# ============================================================
# Application State / Lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize RAG components once when FastAPI starts.

    The expensive components are created once and stored in
    app.state so every request can reuse them.
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


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="RAGnosis AI API",
    description=(
        "Manual-grounded diagnostic API for Dell Precision 5560. "
        "Answers are generated using retrieved information from "
        "the indexed service manual and returned with citations."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ============================================================
# Pydantic Models
# ============================================================

class ChatRequest(BaseModel):
    """
    Request body for the /chat endpoint.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "How do I remove the battery?",
                "top_k": 5,
            }
        }
    )

    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Diagnostic question about the supported Dell manual.",
        examples=[
            "How do I remove the battery?",
            "What does the 2 white and 2 yellow LED pattern mean?",
        ],
    )

    top_k: int = Field(
        default=TOP_K,
        ge=1,
        le=10,
        description="Number of relevant manual chunks to retrieve.",
    )

    @field_validator("query")
    @classmethod
    def validate_query_text(cls, value: str) -> str:
        """
        Basic API-level validation.

        More advanced semantic validation, including prompt-injection
        detection, remains inside agent.policy.
        """

        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value


class CitationOut(BaseModel):
    """
    Citation returned by the RAG system.
    """

    manual: str = Field(
        ...,
        description="Manual identifier.",
        examples=["prec5560-sm-en-us"],
    )

    section: str = Field(
        ...,
        description="Manual section containing the evidence.",
        examples=["Removing the battery"],
    )

    page: int = Field(
        ...,
        ge=1,
        description="Page number containing the evidence.",
        examples=[42],
    )


class ChatResponse(BaseModel):
    """
    Successful /chat response.
    """

    answer: str = Field(
        ...,
        description="Grounded diagnostic answer.",
    )

    citations: list[CitationOut] = Field(
        default_factory=list,
        description="Manual citations supporting the answer.",
    )

    insufficient_evidence: bool = Field(
        ...,
        description="True when the system cannot provide a sufficiently grounded answer.",
    )

    model: str = Field(
        ...,
        description="LLM or refusal model identifier.",
    )


class HealthResponse(BaseModel):
    """
    API health information.
    """

    status: str = Field(
        ...,
        description="API health status.",
        examples=["ok"],
    )

    chunks_indexed: int = Field(
        ...,
        description="Number of chunks currently indexed.",
        examples=[120],
    )

    embed_model: str = Field(
        ...,
        description="Embedding model used by the retrieval layer.",
        examples=["all-MiniLM-L6-v2"],
    )

    collection: str = Field(
        ...,
        description="ChromaDB collection name.",
    )


class ErrorResponse(BaseModel):
    """
    Standard API error format.
    """

    error: str
    message: str
    detail: Any | None = None


# ============================================================
# Exception Handlers
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Convert FastAPI/Pydantic validation errors into a clean,
    predictable JSON response.
    """

    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "The request contains invalid data.",
            "detail": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception,
):
    """
    Prevent internal implementation details from leaking to clients.
    """

    print(f"[ERROR] Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": (
                "An unexpected error occurred while processing "
                "the request."
            ),
        },
    )


# ============================================================
# Root
# ============================================================

@app.get(
    "/",
    tags=["System"],
    summary="API information",
)
async def root():
    """
    Return basic API information.
    """

    return {
        "name": "RAGnosis AI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ============================================================
# Chat
# ============================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Diagnostic"],
    summary="Ask a diagnostic question",
    description=(
        "Submit a Dell Precision 5560 diagnostic question. "
        "The system retrieves relevant manual evidence and "
        "generates a citation-backed response."
    ),
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Invalid request data.",
        },
        500: {
            "model": ErrorResponse,
            "description": "Unexpected server error.",
        },
        503: {
            "model": ErrorResponse,
            "description": "RAG service is unavailable.",
        },
    },
)
async def chat(req: ChatRequest):
    """
    Main RAG endpoint.
    """

    agent: DiagnosticAgent = app.state.agent

    try:
        result = agent.run(req.query)

    except ConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail="The RAG service is currently unavailable.",
        ) from exc

    except TimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="The diagnostic service timed out.",
        ) from exc

    except Exception as exc:
        print(f"[CHAT ERROR] {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to process the diagnostic request.",
        ) from exc

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


# ============================================================
# Health
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Check API and knowledge-base health",
)
async def health():
    """
    Return application health and knowledge-base information.
    """

    store: VectorStore = app.state.store

    try:
        count = store.count()

    except Exception as exc:
        print(f"[HEALTH ERROR] {exc}")

        raise HTTPException(
            status_code=503,
            detail="Vector store is unavailable.",
        ) from exc

    return HealthResponse(
        status="ok",
        chunks_indexed=count,
        embed_model=EMBEDDING_MODEL,
        collection=COLLECTION_NAME,
    )