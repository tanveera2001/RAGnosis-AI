from fastapi import FastAPI

app = FastAPI(title="RAGnosis AI")


@app.get("/")
def root():
    return {
        "message": "Welcome to RAGnosis AI"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }