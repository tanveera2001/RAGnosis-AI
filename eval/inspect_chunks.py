import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNK_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.jsonl"


def main():
    if not CHUNK_FILE.exists():
        print(f"Chunk file not found: {CHUNK_FILE}")
        return

    with open(CHUNK_FILE, "r", encoding="utf-8") as f:
        chunks = [
            json.loads(line)
            for line in f
            if line.strip()
        ]

    print(f"Total chunks: {len(chunks)}")
    print("=" * 80)

    for i, chunk in enumerate(chunks):
        print(f"\n[{i}]")
        print(f"Manual : {chunk.get('manual')}")
        print(f"Section: {chunk.get('section')}")
        print(f"Page   : {chunk.get('page')}")
        print(f"Text   : {chunk.get('text', '')[:300]}")
        print("-" * 80)


if __name__ == "__main__":
    main()