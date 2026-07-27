from __future__ import annotations

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="RAGnosis AI",
    page_icon="🔧",
    layout="wide",
)


def get_health():
    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=5
        )
        return response.json()
    except Exception:
        return {
            "status": "unreachable",
            "chunks_indexed": 0,
            "embed_model": "unknown",
            "collection": "unknown",
        }


def ask_question(
    query: str,
    top_k: int = 5
):
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={
            "query": query,
            "top_k": top_k
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()


# ---------------- Sidebar ----------------

with st.sidebar:

    st.title("RAGnosis AI")

    st.caption(
        "Dell Precision 5560 Diagnostic Assistant"
    )

    st.divider()

    health = get_health()

    status_icon = "🟢" if health["status"] == "ok" else "🔴"

    st.markdown(
        f"{status_icon} **API Status:** {health['status']}"
    )

    st.markdown(
        f"📚 **Chunks Indexed:** {health['chunks_indexed']}"
    )

    st.markdown(
        f"🧠 **Embedding Model:** {health['embed_model']}"
    )

    st.markdown(
        f"🗂️ **Collection:** {health['collection']}"
    )

    st.divider()

    top_k = st.slider(
        "Top-K Retrieval",
        min_value=1,
        max_value=10,
        value=5
    )

    if st.button("Clear Chat"):
        st.session_state["messages"] = []
        st.rerun()


# ---------------- Main UI ----------------

st.title("🔧 RAGnosis AI")

st.caption(
    "Ask questions about the Dell Precision 5560 manual."
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for question, response in st.session_state["messages"]:

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        if response.get("insufficient_evidence"):

            st.error(
                response["answer"]
            )

        else:

            st.markdown(
                response["answer"]
            )

            citations = response.get(
                "citations",
                []
            )

            if citations:

                with st.expander(
                    "📎 Sources",
                    expanded=False
                ):

                    for citation in citations:

                        st.markdown(
                            f"- **Page {citation['page']}** — "
                            f"{citation['section']}"
                        )


query = st.chat_input(
    "Ask a question about the manual..."
)

if query:

    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching manual..."
        ):

            try:

                response = ask_question(
                    query=query,
                    top_k=top_k
                )

            except Exception as e:

                response = {
                    "answer": str(e),
                    "citations": [],
                    "insufficient_evidence": True,
                    "model": "error"
                }

        if response.get(
            "insufficient_evidence"
        ):

            st.error(
                response["answer"]
            )

        else:

            st.markdown(
                response["answer"]
            )

            citations = response.get(
                "citations",
                []
            )

            if citations:

                with st.expander(
                    "📎 Sources",
                    expanded=True
                ):

                    for citation in citations:

                        st.markdown(
                            f"- **Page {citation['page']}** — "
                            f"{citation['section']}"
                        )

    st.session_state["messages"].append(
        (
            query,
            response
        )
    )