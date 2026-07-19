
from pathlib import Path

from pdf_to_text import (
    process_pdf,
    save_jsonl as save_pages_jsonl
)

from chunker import (
    load_jsonl,
    build_chunks,
    save_jsonl as save_chunks_jsonl
)


def main():

    project_root = Path(__file__).resolve().parent.parent

    pdf_path = (
        project_root
        / "data"
        / "raw"
        / "prec5560-sm-en-us.pdf"
    )

    pages_output = (
        project_root
        / "data"
        / "processed"
        / "manual.jsonl"
    )

    chunks_output = (
        project_root
        / "data"
        / "processed"
        / "chunks.jsonl"
    )

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    print("=" * 60)
    print("STEP 1: PDF EXTRACTION")
    print("=" * 60)

    pages = process_pdf(str(pdf_path))

    save_pages_jsonl(
        pages,
        pages_output
    )

    print(f"Processed Pages: {len(pages)}")
    print(f"Saved: {pages_output}")

    print()
    print("=" * 60)
    print("STEP 2: SECTION CHUNKING")
    print("=" * 60)

    page_records = load_jsonl(
        pages_output
    )

    chunks = build_chunks(
        page_records
    )

    save_chunks_jsonl(
        chunks,
        chunks_output
    )

    print(f"Created Chunks: {len(chunks)}")
    print(f"Saved: {chunks_output}")

    print()
    print("=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
