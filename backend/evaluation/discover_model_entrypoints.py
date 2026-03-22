import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "backend" / "evaluation" / "outputs" / "model_entrypoints_discovery.json"

PATTERNS = {
    "ARIMA": [r"\bARIMA\b", r"\bSARIMA\b", r"\bstatsmodels\b"],
    "XGBoost": [r"\bXGBRegressor\b", r"\bxgboost\b", r"\bXGBoost\b"],
    "LSTM": [r"\bLSTM\b", r"\bkeras\b", r"\btensorflow\b", r"\btorch\b"],
    "Hybrid_LSTM_XGBoost": [r"\bHybrid\b", r"\bLSTM.*XGBoost\b", r"\bXGBoost.*LSTM\b"],
    "Agentic_RAG": [r"\bRAG\b", r"\bagent\b", r"\bretriev", r"\bvector\b", r"\bMongoDB\b"],
}

SKIP_PARTS = {".venv", "venv", "__pycache__", "node_modules", ".git"}


def scan_py_file(file_path: Path):
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    hits = {}
    for model_name, regex_list in PATTERNS.items():
        score = 0
        for pattern in regex_list:
            if re.search(pattern, text, flags=re.IGNORECASE):
                score += 1
        if score > 0:
            hits[model_name] = score

    if not hits:
        return None

    signatures = re.findall(r"^(class\s+\w+.*:|def\s+\w+\(.*\):)", text, flags=re.MULTILINE)
    imports = re.findall(r"^(from\s+[\w\.]+\s+import\s+.+|import\s+.+)$", text, flags=re.MULTILINE)

    return {
        "file": str(file_path),
        "score": int(sum(hits.values())),
        "hits": hits,
        "signatures": signatures[:60],
        "imports": imports[:60],
    }


def main():
    candidates = []

    for file_path in ROOT.rglob("*.py"):
        parts_lower = {part.lower() for part in file_path.parts}
        if parts_lower.intersection(SKIP_PARTS):
            continue

        scanned = scan_py_file(file_path)
        if scanned:
            candidates.append(scanned)

    candidates.sort(key=lambda item: item["score"], reverse=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"root": str(ROOT), "candidates": candidates}, indent=2), encoding="utf-8")

    print(f"Discovery complete: {OUT}")
    print(f"Candidate files found: {len(candidates)}")


if __name__ == "__main__":
    main()
