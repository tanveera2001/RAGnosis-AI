
import json
import re
from pathlib import Path


MANUAL_NAME = "prec5560-sm-en-us"


def load_jsonl(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    return records


def split_by_headings(record):
    """
    Split a page into multiple section chunks
    using extracted headings.
    """

    page = record["page"]
    text = record["text"]
    headings = record.get("headings", [])

    if not headings:
        return [{
            "manual": MANUAL_NAME,
            "section": "Unknown",
            "page": page,
            "text": text
        }]

    chunks = []

    positions = []

    lower_text = text.lower()

    for heading in headings:

        idx = lower_text.find(heading.lower())

        if idx >= 0:
            positions.append((idx, heading))

    if not positions:

        return [{
            "manual": MANUAL_NAME,
            "section": headings[0],
            "page": page,
            "text": text
        }]

    positions.sort()

    for i, (start, heading) in enumerate(positions):

        if i < len(positions) - 1:
            end = positions[i + 1][0]
        else:
            end = len(text)

        section_text = text[start:end].strip()

        if len(section_text) < 20:
            continue

        chunks.append({
            "manual": MANUAL_NAME,
            "section": heading,
            "page": page,
            "text": section_text
        })

    return chunks


def build_chunks(records):

    chunks = []

    for record in records:

        page_chunks = split_by_headings(record)

        chunks.extend(page_chunks)

    return chunks


def save_jsonl(records, output_path):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        for record in records:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
            )

            f.write("\n")


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parent.parent

    input_file = (
        project_root
        / "data"
        / "processed"
        / "manual.jsonl"
    )

    output_file = (
        project_root
        / "data"
        / "processed"
        / "chunks.jsonl"
    )

    records = load_jsonl(input_file)

    chunks = build_chunks(records)

    save_jsonl(chunks, output_file)

    print(f"Loaded {len(records)} pages")
    print(f"Created {len(chunks)} section chunks")
    print(f"Saved to: {output_file}")
