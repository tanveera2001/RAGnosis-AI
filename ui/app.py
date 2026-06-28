import streamlit as st

st.title("RAGnosis AI")

query = st.text_input("Enter your question")

if st.button("Ask"):
    st.success("Placeholder response")
    st.write("You asked:")
    st.write(query)