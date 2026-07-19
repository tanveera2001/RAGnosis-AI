from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

# Existing app settings
APP_NAME = os.getenv("APP_NAME")
API_HOST = os.getenv("API_HOST")
API_PORT = int(os.getenv("API_PORT", 8000))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))

# Week 3 RAG settings
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

PROCESSED_DIR = DATA_DIR / "processed"

CHROMA_DIR = DATA_DIR / "chroma"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

COLLECTION_NAME = "dell_manuals"