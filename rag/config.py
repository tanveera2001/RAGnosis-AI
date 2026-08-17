from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Application Settings
# ============================================================

APP_NAME = os.getenv("APP_NAME")

API_HOST = os.getenv("API_HOST")

API_PORT = int(
    os.getenv("API_PORT", "8000")
)

STREAMLIT_PORT = int(
    os.getenv("STREAMLIT_PORT", "8501")
)


# ============================================================
# Project Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"

CHROMA_DIR = DATA_DIR / "chroma"


# ============================================================
# RAG Settings
# ============================================================

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

COLLECTION_NAME = "dell_manuals"

TOP_K = int(
    os.getenv("TOP_K", "5")
)


# ============================================================
# LLM Settings
# ============================================================

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    ""
)

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "meta-llama/llama-3.1-8b-instruct:free"
)


# ============================================================
# Deterministic Generation
# ============================================================

TEMPERATURE = 0.0


# ============================================================
# Week 5 — Guardrail Settings
# ============================================================

RELEVANCE_THRESHOLD = float(
    os.getenv("RELEVANCE_THRESHOLD", "0.75")
)

MIN_QUERY_LENGTH = int(
    os.getenv("MIN_QUERY_LENGTH", "10")
)