import os
import tempfile
from pathlib import Path

path = Path(tempfile.gettempdir()) / "matching_eval.db"
if path.exists():
    path.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{path.as_posix()}"

from evidence_service import rank_evidence
from matching_cases import MATCHING_CASES


correct = 0

for index, case in enumerate(MATCHING_CASES, start=1):
    ranked = rank_evidence(
        case["requirement"],
        [{"id": index, "content": case["content"]}],
        top_k=1,
    )

    if not ranked:
        actual = "missing"
    elif ranked[0]["direct_match"] or ranked[0]["score"] >= 2:
        actual = "matched"
    else:
        actual = "partial"

    print(case["requirement"], actual, case["expected"])
    correct += actual == case["expected"]

accuracy = correct / len(MATCHING_CASES)
print("accuracy:", accuracy)
assert accuracy == 1.0