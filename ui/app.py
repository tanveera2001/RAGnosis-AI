from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


# ============================================================
# Configuration
# ============================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000",
)

CHAT_TIMEOUT = 120
HEALTH_TIMEOUT = 5


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="RAGnosis AI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Custom CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- Global ---------- */

    .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* ---------- Header ---------- */

    .app-header {
        padding: 1rem 0 1.5rem 0;
    }

    .app-title {
        font-size: 2.4rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 0;
    }

    /* ---------- Status ---------- */

    .status-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 0.9rem;
        margin-bottom: 0.75rem;
    }

    .status-online {
        color: #15803d;
        font-weight: 700;
    }

    .status-offline {
        color: #dc2626;
        font-weight: 700;
    }

    /* ---------- Citation ---------- */

    .citation-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.6rem;
        background: rgba(128, 128, 128, 0.04);
    }

    .citation-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #6b7280;
    }

    .citation-title {
        font-weight: 650;
        margin-top: 0.2rem;
    }

    .citation-meta {
        color: #6b7280;
        font-size: 0.85rem;
        margin-top: 0.2rem;
    }

    /* ---------- Welcome ---------- */

    .welcome-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0 1.5rem 0;
    }

    .welcome-card h3 {
        margin-top: 0;
    }

    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.15);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API Functions
# ============================================================

def get_health() -> dict[str, Any]:
    """
    Fetch API health information.

    Returns a predictable fallback structure when the API
    cannot be reached.
    """

    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=HEALTH_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        return {
            "status": data.get("status", "unknown"),
            "chunks_indexed": data.get("chunks_indexed", 0),
            "embed_model": data.get("embed_model", "unknown"),
            "collection": data.get("collection", "unknown"),
            "error": None,
        }

    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "chunks_indexed": 0,
            "embed_model": "unknown",
            "collection": "unknown",
            "error": "The API health check timed out.",
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "chunks_indexed": 0,
            "embed_model": "unknown",
            "collection": "unknown",
            "error": "Cannot connect to the FastAPI server.",
        }

    except requests.exceptions.HTTPError as exc:
        return {
            "status": "error",
            "chunks_indexed": 0,
            "embed_model": "unknown",
            "collection": "unknown",
            "error": f"API returned an HTTP error: {exc}",
        }

    except Exception as exc:
        return {
            "status": "error",
            "chunks_indexed": 0,
            "embed_model": "unknown",
            "collection": "unknown",
            "error": str(exc),
        }


def ask_question(
    query: str,
    top_k: int,
) -> dict[str, Any]:
    """
    Send a diagnostic question to FastAPI.
    """

    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={
            "query": query,
            "top_k": top_k,
        },
        timeout=CHAT_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# Session State
# ============================================================

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "top_k" not in st.session_state:
    st.session_state["top_k"] = 5


# ============================================================
# Sidebar
# ============================================================

health = get_health()

with st.sidebar:

    st.title("🔧 RAGnosis AI")

    st.caption(
        "Dell Precision 5560 Diagnostic Assistant"
    )

    st.divider()

    # --------------------------------------------------------
    # API Status
    # --------------------------------------------------------

    st.subheader("System Status")

    if health["status"] == "ok":

        st.markdown(
            '<div class="status-card">'
            '<span class="status-online">● API Online</span>'
            "</div>",
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            '<div class="status-card">'
            '<span class="status-offline">● API Unavailable</span>'
            "</div>",
            unsafe_allow_html=True,
        )

        if health["error"]:
            st.caption(health["error"])

    # --------------------------------------------------------
    # Knowledge Base
    # --------------------------------------------------------

    st.subheader("Knowledge Base")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Chunks",
            health["chunks_indexed"],
        )

    with col2:
        st.metric(
            "Top-K",
            st.session_state["top_k"],
        )

    st.caption(
        f"Embedding: `{health['embed_model']}`"
    )

    st.caption(
        f"Collection: `{health['collection']}`"
    )

    st.divider()

    # --------------------------------------------------------
    # Retrieval Settings
    # --------------------------------------------------------

    st.subheader("Retrieval")

    top_k = st.slider(
        "Number of chunks",
        min_value=1,
        max_value=10,
        value=st.session_state["top_k"],
        help=(
            "Controls how many manual chunks are retrieved "
            "before generating the answer."
        ),
    )

    st.session_state["top_k"] = top_k

    st.divider()

    # --------------------------------------------------------
    # Chat Controls
    # --------------------------------------------------------

    st.subheader("Chat")

    if st.button(
        "🗑️ Clear conversation",
        use_container_width=True,
    ):
        st.session_state["messages"] = []
        st.rerun()

    if st.button(
        "🔄 Refresh system status",
        use_container_width=True,
    ):
        st.rerun()

    st.divider()

    st.caption(
        "RAGnosis AI answers only from indexed manual evidence."
    )


# ============================================================
# Main Header
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">🔧 RAGnosis AI</div>
        <p class="app-subtitle">
            Manual-grounded diagnostic assistant for Dell Precision 5560
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Welcome State
# ============================================================

if not st.session_state["messages"]:

    st.markdown(
        """
        <div class="welcome-card">

        ### Welcome to RAGnosis AI 👋

        Ask a question about the Dell Precision 5560 service manual.

        **Examples**

        - What does the 2 white and 2 yellow LED pattern mean?
        - How do I remove the battery?
        - How do I perform BIOS recovery?
        - What are the steps for removing the heat sink?

        Every supported answer is grounded in retrieved manual
        evidence and includes citations.

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Citation Renderer
# ============================================================

def render_citations(
    citations: list[dict[str, Any]],
) -> None:
    """
    Render citations as professional source cards.
    """
    if not citations:
        return

    st.markdown("#### 📚 Sources")

    for index, citation in enumerate(citations, start=1):
        manual = citation.get("manual", "Unknown manual")
        section = citation.get("section", "Unknown section")
        page = citation.get("page", "?")

        # Keep the HTML string compact or cleanly joined to prevent raw text rendering
        card_html = (
            f'<div class="citation-card">'
            f'  <div class="citation-label">Source {index}</div>'
            f'  <div class="citation-title">{section}</div>'
            f'  <div class="citation-meta">Manual: {manual} &nbsp; • &nbsp; Page: {page}</div>'
            f'</div>'
        )

        st.markdown(card_html, unsafe_allow_html=True)


# ============================================================
# Message Renderer
# ============================================================

def render_message(
    question: str,
    response: dict[str, Any],
) -> None:

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        if response.get("insufficient_evidence"):

            st.warning(
                response.get(
                    "answer",
                    "The manual does not contain enough evidence.",
                )
            )

        else:

            st.markdown(
                response.get(
                    "answer",
                    "No answer was returned.",
                )
            )

        citations = response.get(
            "citations",
            [],
        )

        render_citations(citations)

        model = response.get(
            "model",
            "unknown",
        )

        st.caption(
            f"Model: `{model}`"
        )


# ============================================================
# Existing Conversation
# ============================================================

for message in st.session_state["messages"]:

    render_message(
        question=message["question"],
        response=message["response"],
    )


# ============================================================
# Chat Input
# ============================================================

query = st.chat_input(
    "Describe your Dell Precision 5560 problem..."
)


# ============================================================
# Process New Question
# ============================================================

if query:

    query = query.strip()

    if not query:

        st.warning(
            "Please enter a diagnostic question."
        )

        st.stop()

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):

        response = None

        try:

            with st.spinner(
                "🔎 Searching the service manual and preparing a grounded answer..."
            ):

                response = ask_question(
                    query=query,
                    top_k=st.session_state["top_k"],
                )

        except requests.exceptions.Timeout:

            st.error(
                "The diagnostic request timed out. "
                "Please try again."
            )

            response = {
                "answer": (
                    "The diagnostic service timed out."
                ),
                "citations": [],
                "insufficient_evidence": True,
                "model": "error",
            }

        except requests.exceptions.ConnectionError:

            st.error(
                "Cannot connect to the FastAPI backend. "
                "Please make sure the API service is running."
            )

            response = {
                "answer": (
                    "The FastAPI backend is unreachable."
                ),
                "citations": [],
                "insufficient_evidence": True,
                "model": "error",
            }

        except requests.exceptions.HTTPError as exc:

            error_message = (
                "The API rejected the request."
            )

            try:
                error_data = exc.response.json()

                if "message" in error_data:
                    error_message = error_data["message"]

                elif "detail" in error_data:
                    error_message = str(
                        error_data["detail"]
                    )

            except Exception:
                pass

            st.error(error_message)

            response = {
                "answer": error_message,
                "citations": [],
                "insufficient_evidence": True,
                "model": "error",
            }

        except Exception as exc:

            st.error(
                "An unexpected error occurred."
            )

            response = {
                "answer": str(exc),
                "citations": [],
                "insufficient_evidence": True,
                "model": "error",
            }

        if response:

            if response.get("insufficient_evidence"):

                st.warning(
                    response.get(
                        "answer",
                        "Insufficient evidence.",
                    )
                )

            else:

                st.markdown(
                    response.get(
                        "answer",
                        "No answer returned.",
                    )
                )

            citations = response.get(
                "citations",
                [],
            )

            render_citations(citations)

            st.caption(
                f"Model: `{response.get('model', 'unknown')}`"
            )

            st.session_state["messages"].append(
                {
                    "question": query,
                    "response": response,
                }
            )