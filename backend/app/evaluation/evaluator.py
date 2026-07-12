import sys
import json
sys.path.insert(0, ".")

from app.github_client.client import clone_repo
from app.agents.code_agent import run as run_code_agent
from app.agents.reviewer import run as run_reviewer
from app.evaluation.test_cases import TEST_CASES
from app.rag.ingest import ingest_repo


def evaluate():
    results = []

    for case in TEST_CASES:
        print(f"\n--- Case: {case['question'][:60]}... ---")
        repo_id, _ = clone_repo(case["repo_url"])
        ingest_repo(repo_id)

        claim = run_code_agent(repo_id, case["question"])
        review = run_reviewer(repo_id, claim)

        cited_files = {ev.file_path for ev in claim.evidence}
        expected = set(case["expected_evidence_files"])
        hits = cited_files & expected
        precision = len(hits) / len(cited_files) if cited_files else 0.0
        recall = len(hits) / len(expected) if expected else 0.0

        result = {
            "question": case["question"],
            "cited_files": sorted(cited_files),
            "expected_files": sorted(expected),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "reviewer_verdict": review.get("verdict", "unknown"),
            "confidence": claim.confidence,
        }
        results.append(result)
        print(json.dumps(result, indent=2))

    print("\n=== Summary ===")
    avg_precision = sum(r["precision"] for r in results) / len(results) if results else 0
    avg_recall = sum(r["recall"] for r in results) / len(results) if results else 0
    print(f"Average precision: {avg_precision:.2f}")
    print(f"Average recall:    {avg_recall:.2f}")
    flagged = [r for r in results if r["precision"] < 0.5]
    if flagged:
        print(f"Flagged cases (precision < 0.5): {len(flagged)}")
        for f in flagged:
            print(f"  - {f['question'][:60]}")

    return results


if __name__ == "__main__":
    evaluate()
