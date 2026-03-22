from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

LIKERT_MIN = 1
LIKERT_MAX = 5
DEFAULT_POLICY_TERMS = {
    "policy", "policies", "regulation", "regulatory", "subsidy", "subsidies", "incentive", "incentives",
    "mandate", "tax", "duty", "import", "ev", "electric", "battery", "charging", "fame", "oem",
    "adoption", "compliance", "emission", "manufacturing", "localization", "scheme", "support"
}
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "is", "are", "was", "were",
    "be", "by", "this", "that", "it", "as", "at", "from", "can", "could", "should", "would", "will",
    "may", "might", "about", "into", "over", "under", "than", "then", "their", "there", "these", "those"
}


@dataclass
class ExplanationRecord:
    explanation_id: str
    explanation: str
    retrieved_context: str
    policy_context: str = ""
    metadata: Optional[Dict[str, Any]] = None


def _normalize_text(text: Any) -> str:
    if text is None:
        return ""
    if isinstance(text, list):
        return "\n".join(str(item) for item in text)
    return str(text)


def _sentence_split(text: str) -> List[str]:
    text = _normalize_text(text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def _tokenize(text: str) -> List[str]:
    text = _normalize_text(text).lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return [tok for tok in tokens if tok not in STOPWORDS]


def _unique_tokens(text: str) -> set[str]:
    return set(_tokenize(text))


def _extract_policy_terms(policy_context: str) -> set[str]:
    terms = set(DEFAULT_POLICY_TERMS)
    terms.update(_unique_tokens(policy_context))
    return {term for term in terms if len(term) >= 3}


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return float(num / den)


def _clamp_likert(value: float) -> int:
    return int(max(LIKERT_MIN, min(LIKERT_MAX, round(value))))


def _sentence_support_ratio(sentence: str, context_tokens: set[str], policy_tokens: set[str]) -> float:
    sent_tokens = _unique_tokens(sentence)
    if not sent_tokens:
        return 0.0
    supported = len(sent_tokens.intersection(context_tokens.union(policy_tokens)))
    return _safe_div(supported, len(sent_tokens))


def _score_context_relevance(explanation: str, context: str, policy_context: str, rater: str) -> int:
    context_tokens = _unique_tokens(context)
    policy_tokens = _extract_policy_terms(policy_context)
    explanation_tokens = _unique_tokens(explanation)
    if not explanation_tokens:
        return 1

    overlap = _safe_div(len(explanation_tokens.intersection(context_tokens)), len(explanation_tokens))
    sentence_support = np.mean([
        _sentence_support_ratio(sent, context_tokens, set()) for sent in _sentence_split(explanation)
    ]) if _sentence_split(explanation) else 0.0

    if rater == "A":
        raw = 1 + 4 * (0.65 * overlap + 0.35 * sentence_support)
    else:
        policy_bonus = _safe_div(len(explanation_tokens.intersection(policy_tokens)), max(len(explanation_tokens), 1))
        raw = 1 + 4 * (0.45 * overlap + 0.45 * sentence_support + 0.10 * policy_bonus)
    return _clamp_likert(raw)


def _score_policy_alignment(explanation: str, policy_context: str, rater: str) -> int:
    explanation_tokens = _unique_tokens(explanation)
    policy_tokens = _extract_policy_terms(policy_context)
    if not explanation_tokens:
        return 1

    policy_overlap = _safe_div(len(explanation_tokens.intersection(policy_tokens)), len(explanation_tokens))
    sentence_hits = []
    for sent in _sentence_split(explanation):
        sent_tokens = _unique_tokens(sent)
        sentence_hits.append(1.0 if sent_tokens.intersection(policy_tokens) else 0.0)
    policy_sentence_ratio = float(np.mean(sentence_hits)) if sentence_hits else 0.0

    if rater == "A":
        raw = 1 + 4 * (0.70 * policy_overlap + 0.30 * policy_sentence_ratio)
    else:
        raw = 1 + 4 * (0.55 * policy_overlap + 0.45 * policy_sentence_ratio)
    return _clamp_likert(raw)


def _score_clarity_interpretability(explanation: str, rater: str) -> int:
    sentences = _sentence_split(explanation)
    words = _tokenize(explanation)
    if not words:
        return 1

    avg_sentence_len = _safe_div(len(words), max(len(sentences), 1))
    numbered_structure = 1.0 if re.search(r"(^|\n)\s*(\d+\.|[-*])", explanation) else 0.0
    connector_ratio = _safe_div(
        len(re.findall(r"\b(because|therefore|thus|due to|driven by|as a result|indicates)\b", explanation.lower())),
        max(len(sentences), 1),
    )
    jargon_penalty = _safe_div(len([w for w in words if len(w) > 14]), len(words))

    len_score = 1.0
    if avg_sentence_len > 26:
        len_score = 0.55
    elif avg_sentence_len > 20:
        len_score = 0.75
    elif avg_sentence_len < 6:
        len_score = 0.70

    if rater == "A":
        raw = 1 + 4 * (0.45 * len_score + 0.30 * min(connector_ratio, 1.0) + 0.25 * numbered_structure - 0.20 * jargon_penalty)
    else:
        raw = 1 + 4 * (0.55 * len_score + 0.20 * min(connector_ratio, 1.0) + 0.25 * numbered_structure - 0.15 * jargon_penalty)
    return _clamp_likert(raw)


def _hallucination_rate(explanation: str, context: str, policy_context: str) -> float:
    sentences = _sentence_split(explanation)
    if not sentences:
        return 1.0

    context_tokens = _unique_tokens(context)
    policy_tokens = _extract_policy_terms(policy_context)
    unsupported = 0
    for sent in sentences:
        if _sentence_support_ratio(sent, context_tokens, policy_tokens) < 0.20:
            unsupported += 1
    return float(unsupported / len(sentences))


def _safe_kappa(y_true: pd.Series, y_pred: pd.Series) -> float:
    true_values = list(y_true)
    pred_values = list(y_pred)
    if not true_values or not pred_values:
        return float("nan")
    if len(set(true_values).union(set(pred_values))) <= 1:
        return 1.0 if true_values == pred_values else 0.0
    return float(cohen_kappa_score(true_values, pred_values))


def _cohen_kappa_for_frames(frame: pd.DataFrame) -> Dict[str, float]:
    result = {}
    for metric in ["CR", "PA", "CI"]:
        result[metric] = _safe_kappa(frame[f"{metric}_rater_a"], frame[f"{metric}_rater_b"])
    stacked_a = pd.concat([frame["CR_rater_a"], frame["PA_rater_a"], frame["CI_rater_a"]], ignore_index=True)
    stacked_b = pd.concat([frame["CR_rater_b"], frame["PA_rater_b"], frame["CI_rater_b"]], ignore_index=True)
    result["overall"] = _safe_kappa(stacked_a, stacked_b)
    return result


def _coerce_records(records: Sequence[Dict[str, Any]]) -> List[ExplanationRecord]:
    coerced = []
    for idx, record in enumerate(records, start=1):
        explanation_id = str(record.get("explanation_id") or record.get("id") or f"exp_{idx}")
        explanation = _normalize_text(record.get("explanation") or record.get("generated_explanation") or record.get("response"))
        retrieved_context = _normalize_text(
            record.get("retrieved_context") or record.get("context") or record.get("source_context") or record.get("sources")
        )
        policy_context = _normalize_text(record.get("policy_context") or record.get("policy_sources") or "")
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        coerced.append(
            ExplanationRecord(
                explanation_id=explanation_id,
                explanation=explanation,
                retrieved_context=retrieved_context,
                policy_context=policy_context,
                metadata=metadata,
            )
        )
    return coerced


def evaluate_explanation_grounding(records: Sequence[Dict[str, Any]]) -> Dict[str, pd.DataFrame]:
    explanation_records = _coerce_records(records)
    rows: List[Dict[str, Any]] = []

    for rec in explanation_records:
        cr_a = _score_context_relevance(rec.explanation, rec.retrieved_context, rec.policy_context, rater="A")
        cr_b = _score_context_relevance(rec.explanation, rec.retrieved_context, rec.policy_context, rater="B")
        pa_a = _score_policy_alignment(rec.explanation, rec.policy_context, rater="A")
        pa_b = _score_policy_alignment(rec.explanation, rec.policy_context, rater="B")
        ci_a = _score_clarity_interpretability(rec.explanation, rater="A")
        ci_b = _score_clarity_interpretability(rec.explanation, rater="B")

        cr = float(np.mean([cr_a, cr_b]))
        pa = float(np.mean([pa_a, pa_b]))
        ci = float(np.mean([ci_a, ci_b]))
        composite = float(np.mean([cr, pa, ci]))
        normalized = float(((composite - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN)) * 100.0)
        hallucination = _hallucination_rate(rec.explanation, rec.retrieved_context, rec.policy_context)

        rows.append(
            {
                "Explanation ID": rec.explanation_id,
                "CR_rater_a": cr_a,
                "CR_rater_b": cr_b,
                "CR": round(cr, 3),
                "PA_rater_a": pa_a,
                "PA_rater_b": pa_b,
                "PA": round(pa, 3),
                "CI_rater_a": ci_a,
                "CI_rater_b": ci_b,
                "CI": round(ci, 3),
                "Composite Explainability Score": round(composite, 3),
                "Normalized Score (0-100)": round(normalized, 3),
                "Hallucination Rate": round(hallucination, 4),
                "Explanation Length": len(_tokenize(rec.explanation)),
            }
        )

    details_df = pd.DataFrame(rows)
    if details_df.empty:
        summary_df = pd.DataFrame(
            [
                {
                    "Metric": "No data",
                    "Mean": np.nan,
                    "Std": np.nan,
                    "Cohen's Kappa": np.nan,
                }
            ]
        )
        return {"details": details_df, "summary": summary_df}

    kappas = _cohen_kappa_for_frames(details_df)
    summary_rows = [
        {"Metric": "Context Relevance (CR)", "Mean": details_df["CR"].mean(), "Std": details_df["CR"].std(ddof=0), "Cohen's Kappa": kappas["CR"]},
        {"Metric": "Policy Alignment (PA)", "Mean": details_df["PA"].mean(), "Std": details_df["PA"].std(ddof=0), "Cohen's Kappa": kappas["PA"]},
        {"Metric": "Clarity and Interpretability (CI)", "Mean": details_df["CI"].mean(), "Std": details_df["CI"].std(ddof=0), "Cohen's Kappa": kappas["CI"]},
        {
            "Metric": "Composite Explainability Score",
            "Mean": details_df["Composite Explainability Score"].mean(),
            "Std": details_df["Composite Explainability Score"].std(ddof=0),
            "Cohen's Kappa": kappas["overall"],
        },
        {
            "Metric": "Normalized Score (0-100)",
            "Mean": details_df["Normalized Score (0-100)"].mean(),
            "Std": details_df["Normalized Score (0-100)"].std(ddof=0),
            "Cohen's Kappa": kappas["overall"],
        },
        {
            "Metric": "Hallucination Rate",
            "Mean": details_df["Hallucination Rate"].mean(),
            "Std": details_df["Hallucination Rate"].std(ddof=0),
            "Cohen's Kappa": np.nan,
        },
    ]
    summary_df = pd.DataFrame(summary_rows)

    return {
        "details": details_df,
        "summary": summary_df,
    }
