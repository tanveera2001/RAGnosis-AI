import requests
import streamlit as st

st.title("RAGnosis AI")

query = st.text_input("Question")

if st.button("Ask"):

    response = requests.get(
        "http://localhost:8000/"
    )

    st.write(response.json())