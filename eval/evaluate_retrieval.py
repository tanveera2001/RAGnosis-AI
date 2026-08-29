import sys
import json
from pathlib import Path
from statistics import mean


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from rag.retriever import Retriever
from rag.vectorstore import VectorStore


QUESTIONS_FILE = (
    PROJECT_ROOT
    / "eval"
    / "questions.jsonl"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "eval"
    / "results"
)


def load_questions():
    with open(
        QUESTIONS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def source_key(source):
    return (
        source.get("manual"),
        source.get("section"),
        source.get("page"),
    )


def chunk_key(chunk):
    return (
        chunk.get("manual"),
        chunk.get("section"),
        chunk.get("page"),
    )


def is_relevant(
    chunk,
    expected_sources
):
    retrieved = chunk_key(chunk)

    expected = {
        source_key(source)
        for source in expected_sources
    }

    return retrieved in expected


def calculate_metrics(
    chunks,
    expected_sources
):

    if not expected_sources:

        return {
            "hit_at_1": None,
            "hit_at_3": None,
            "hit_at_5": None,
            "hit_at_8": None,
            "precision_at_5": None,
            "recall_at_5": None,
        }

    relevant = [
        is_relevant(
            chunk,
            expected_sources
        )
        for chunk in chunks
    ]

    def hit_at(k):

        return int(
            any(
                relevant[:k]
            )
        )

    k = min(
        5,
        len(chunks)
    )

    relevant_count = sum(
        relevant[:k]
    )

    precision = (
        relevant_count / k
        if k > 0
        else 0.0
    )

    expected_count = len(
        expected_sources
    )

    retrieved_expected = len(
        {
            chunk_key(chunk)
            for chunk, rel
            in zip(
                chunks[:k],
                relevant[:k]
            )
            if rel
        }
    )

    recall = (
        retrieved_expected
        / expected_count
        if expected_count > 0
        else 0.0
    )

    return {
        "hit_at_1": hit_at(1),
        "hit_at_3": hit_at(3),
        "hit_at_5": hit_at(5),
        "hit_at_8": hit_at(8),
        "precision_at_5": precision,
        "recall_at_5": recall,
    }


def main():

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    questions = load_questions()

    print(
        f"Loaded evaluation questions: "
        f"{len(questions)}"
    )

    store = VectorStore()

    retriever = Retriever(
        store=store,
        top_k=8
    )

    all_results = []

    for item in questions:

        if not item.get(
            "should_answer",
            True
        ):
            print(
                f"{item['id']} | "
                f"Skipped "
                f"(should_answer=false)"
            )
            continue

        expected_sources = item.get(
            "expected_sources",
            []
        )

        if not expected_sources:

            print(
                f"{item['id']} | "
                f"Skipped "
                f"(no expected sources)"
            )

            continue

        print(
            f"\nEvaluating {item['id']}: "
            f"{item['question']}"
        )

        chunks = retriever.retrieve(
            query=item["question"],
            top_k=8
        )

        metrics = calculate_metrics(
            chunks,
            expected_sources
        )

        result = {

            "id": item["id"],

            "category": item[
                "category"
            ],

            "question": item[
                "question"
            ],

            "expected_sources":
                expected_sources,

            "retrieved_sources": [

                {
                    "manual":
                        chunk.get(
                            "manual"
                        ),

                    "section":
                        chunk.get(
                            "section"
                        ),

                    "page":
                        chunk.get(
                            "page"
                        ),

                    "distance":
                        chunk.get(
                            "distance"
                        ),
                }

                for chunk in chunks
            ],

            "metrics": metrics,
        }

        all_results.append(
            result
        )

        print(
            f"  Hit@1: "
            f"{metrics['hit_at_1']}"

        )

        print(
            f"  Hit@3: "
            f"{metrics['hit_at_3']}"

        )

        print(
            f"  Hit@5: "
            f"{metrics['hit_at_5']}"

        )

        print(
            f"  Hit@8: "
            f"{metrics['hit_at_8']}"
        )

    if not all_results:

        print(
            "\nNo evaluable questions found."
        )

        return

    metric_names = [

        "hit_at_1",
        "hit_at_3",
        "hit_at_5",
        "hit_at_8",
        "precision_at_5",
        "recall_at_5",
    ]

    summary = {}

    for metric in metric_names:

        values = [

            result["metrics"][metric]

            for result
            in all_results

            if result[
                "metrics"
            ][metric] is not None

        ]

        summary[metric] = (

            mean(values)

            if values

            else None

        )

    output = {

        "summary": summary,

        "questions": all_results

    }

    output_file = (

        RESULTS_DIR
        / "retrieval_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(
        "=" * 60
    )
    print(
        "RETRIEVAL EVALUATION SUMMARY"
    )
    print(
        "=" * 60
    )

    for key, value in summary.items():

        if value is not None:

            print(
                f"{key}: "
                f"{value * 100:.2f}%"
            )

    print()
    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    main()