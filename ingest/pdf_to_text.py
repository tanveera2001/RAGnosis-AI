
import fitz
import re
import json
from pathlib import Path
from collections import Counter


WARNING_PATTERN = re.compile(
    r"\b(?:warning|caution|note)\b",
    re.IGNORECASE
)

STEP_PATTERNS = [
    r"^\d+\.",
    r"^\d+\)",
    r"^step\s+\d+"
]

PAGE_NUMBER_PATTERNS = [
    r"^page\s+\d+$",
    r"^\d+$"
]


def fix_encoding(text):
    """
    Fix common PDF encoding artifacts.
    """

    replacements = {
        "Â©": "©",
        "â€”": "—",
        "â€“": "–",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"'
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def extract_pdf(pdf_path):
    """
    Extract raw text from every page.
    """
    doc = fitz.open(pdf_path)

    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        pages.append({
            "page": page_num + 1,
            "text": page.get_text()
        })

    doc.close()

    return pages


def is_page_number(line):
    """
    Detect page numbers like:
    Page 10
    10
    """

    line = line.strip().lower()

    for pattern in PAGE_NUMBER_PATTERNS:
        if re.match(pattern, line):
            return True

    return False


def find_repeated_lines(pages, threshold=0.8):
    """
    Detect repeated headers/footers.

    If a line appears on >=80% pages,
    treat it as noise.
    """

    counter = Counter()

    total_pages = len(pages)

    for page in pages:

        unique_lines = set()

        for line in page["text"].splitlines():

            line = line.strip()

            if line:
                unique_lines.add(line)

        for line in unique_lines:
            counter[line] += 1

    repeated_lines = set()

    for line, count in counter.items():

        if count >= total_pages * threshold:
            repeated_lines.add(line)

    return repeated_lines


def clean_text(text, repeated_lines):
    """
    Remove:
    - blank lines
    - page numbers
    - repeated headers/footers
    """

    cleaned = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line in repeated_lines:
            continue

        if is_page_number(line):
            continue

        cleaned.append(line)

    return "\n".join(cleaned)


def extract_headings(page):
    """
    Detect headings using font size.
    """

    headings = []

    try:

        data = page.get_text("dict")

        for block in data.get("blocks", []):

            if "lines" not in block:
                continue

            for line in block["lines"]:

                for span in line.get("spans", []):

                    text = span.get("text", "").strip()
                    size = span.get("size", 0)

                    if not text:
                        continue

                    if size >= 14:
                        headings.append(text)

    except Exception:
        pass

    return list(dict.fromkeys(headings))


def extract_warnings(text):
    """
    Extract WARNING / CAUTION / NOTE lines.
    Avoid false positives such as:
    precautions
    notification
    notebook
    """

    warnings = []

    for line in text.splitlines():

        if WARNING_PATTERN.search(line):
            warnings.append(line)

    return warnings


def extract_steps(text):
    """
    Extract numbered procedure steps.
    """

    steps = []

    for line in text.splitlines():

        line = line.strip()

        for pattern in STEP_PATTERNS:

            if re.match(pattern, line, re.IGNORECASE):
                steps.append(line)
                break

    return steps


def process_pdf(pdf_path):
    """
    Main processing pipeline.
    """

    doc = fitz.open(pdf_path)

    raw_pages = []

    # Pass 1: collect text
    for page_num in range(len(doc)):

        page = doc[page_num]

        raw_pages.append({
            "page": page_num + 1,
            "text": page.get_text()
        })

    repeated_lines = find_repeated_lines(raw_pages)

    records = []

    # Pass 2: structured extraction
    for page_num in range(len(doc)):

        page = doc[page_num]

        raw_text = page.get_text()

        cleaned_text = clean_text(
            raw_text,
            repeated_lines
        )

        cleaned_text = fix_encoding(cleaned_text)

        if len(cleaned_text.strip()) == 0:
            continue

        headings = extract_headings(page)

        warnings = extract_warnings(cleaned_text)

        steps = extract_steps(cleaned_text)

        record = {
            "page": page_num + 1,
            "headings": headings,
            "warnings": warnings,
            "steps": steps,
            "text": cleaned_text
        }

        records.append(record)

    doc.close()

    return records


def save_jsonl(records, output_path):
    """
    Save records to JSONL.
    """

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

    pdf_path = (
        project_root
        / "data"
        / "raw"
        / "prec5560-sm-en-us.pdf"
    )

    output_path = (
        project_root
        / "data"
        / "processed"
        / "manual.jsonl"
    )

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    print(f"Reading PDF: {pdf_path}")

    records = process_pdf(str(pdf_path))

    save_jsonl(records, output_path)

    print(f"Processed {len(records)} pages")
    print(f"Saved JSONL to: {output_path}")

