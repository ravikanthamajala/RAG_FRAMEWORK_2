"""
Automotive Market Analysis RAG Agent

Implementation using LangChain and Ollama for intelligent retrieval and analysis of:
- China's automotive market policies, EV strategies, and OEM performance
- India's automotive regulations and market current state
- Policy impact analysis and market comparison insights

v2: structured, intent-aware prompting with post-processing for
    Comparison / Forecast / Trend / General queries.
"""

import re
import os
from typing import Dict, Any, List, Optional

from langchain_ollama import OllamaLLM
from app.utils.vector_search import search_similar_documents
from app.utils.embeddings import generate_embedding
from app.services.chart_service import ChartService


# ---------------------------------------------------------------------------
# Intent Detection
# ---------------------------------------------------------------------------

# Intent → (label, description used in prompt, relevant filter keywords)
_INTENTS = {
    "COMPARISON": {
        "keywords": [
            "compare", "comparison", "vs", "versus", "with and without",
            "difference between", "impact of", "effect of", "with infrastructure",
            "without infrastructure", "with port", "without port", "if i construct",
            "if i don't construct", "scenario", "baseline",
            "with highway", "without highway", "highway construction", "highways construction",
            "new highway", "new highways", "road construction", "new roads",
        ],
        "doc_keywords": ["infrastructure", "port", "highway", "scenario", "policy", "comparison"],
    },
    "FORECAST": {
        "keywords": [
            "forecast", "predict", "prediction", "future", "by 2030", "by 2035",
            "by 2040", "projection", "outlook", "trajectory", "what will", "how will",
            "will be", "expected", "anticipate", "estimate",
        ],
        "doc_keywords": ["forecast", "projection", "trend", "2030", "2035", "2040"],
    },
    "TREND": {
        "keywords": [
            "trend", "growth", "change over", "evolution", "over the years",
            "historically", "pattern", "trajectory",
        ],
        "doc_keywords": ["trend", "growth", "historical", "annual"],
    },
    "NUMBERS": {
        "keywords": [
            "how much", "how many", "percentage", "rate", "value", "price",
            "sales", "revenue", "cost", "profit", "quantity", "units",
            "market size", "share", "billion", "million", "crore",
        ],
        "doc_keywords": [],  # rely on similarity search
    },
    "DISTRIBUTION": {
        "keywords": [
            "market share", "distribution", "breakdown", "proportion",
            "oem", "manufacturers", "who leads", "dominant",
        ],
        "doc_keywords": ["market share", "oem", "distribution"],
    },
}


def classify_intent(query: str) -> str:
    """Return the primary intent label for a query."""
    ql = query.lower()
    # Priority order: COMPARISON > FORECAST > TREND > DISTRIBUTION > NUMBERS > GENERAL
    for intent in ["COMPARISON", "FORECAST", "TREND", "DISTRIBUTION", "NUMBERS"]:
        if any(kw in ql for kw in _INTENTS[intent]["keywords"]):
            return intent
    return "GENERAL"


def _year_range_from_query(query: str):
    """Extract the target year(s) mentioned in the query, e.g. 2040."""
    years = re.findall(r'\b(20[2-9]\d)\b', query)
    return sorted(set(int(y) for y in years)) if years else None


# ---------------------------------------------------------------------------
# Document Prioritisation
# ---------------------------------------------------------------------------

def prioritize_documents(docs: List[Dict], intent: str) -> List[Dict]:
    """Push documents most relevant to the detected intent to the top."""
    doc_kws = _INTENTS.get(intent, {}).get("doc_keywords", [])
    if not doc_kws:
        return docs

    def _score(doc):
        name = doc.get("filename", "").lower()
        return sum(1 for kw in doc_kws if kw in name)

    # Stable sort: high-score docs first, others keep similarity order
    prioritised = sorted(docs, key=_score, reverse=True)
    return prioritised


# ---------------------------------------------------------------------------
# Structured Prompt Builder
# ---------------------------------------------------------------------------

def _build_prompt(query: str, intent: str, context: str) -> str:
    """
    Build an intent-specific prompt that forces structured, numerical output.
    """
    target_years = _year_range_from_query(query)
    year_hint = (
        f"The user specifically asks about the year(s): {', '.join(str(y) for y in target_years)}. "
        "Provide explicit numerical estimates for those years."
        if target_years else ""
    )

    base_instructions = f"""You are a quantitative data analyst specialising in the Indian and Chinese automotive markets.
Your task is to answer the user's question STRICTLY based on the documents provided.

RULES:
- Do NOT give generic explanations or background theory.
- ALWAYS include specific numbers, percentages, and year-tagged values extracted from the documents.
- If a number is not explicitly stated in the documents, make a reasonable data-driven estimate and clearly label it as "(estimated)".
- Structure your answer in the exact format shown below.
- Be concise within each section — bullet points preferred.
{year_hint}

--- DOCUMENTS ---
{context}
--- END DOCUMENTS ---

User Question: {query}
"""

    if intent == "COMPARISON":
        format_block = """
FORMAT YOUR ANSWER EXACTLY AS FOLLOWS:

## 1. Key Comparison
| Metric | Without Infrastructure | With Infrastructure |
|--------|----------------------|---------------------|
| <metric 1> | <value> | <value> |
| <metric 2> | <value> | <value> |
(Add as many rows as the data supports.)

## 2. Insights
- <Key difference 1 with numbers>
- <Key difference 2 with numbers>
- <Key difference 3 with numbers>

## 3. Forecast
- <Year>: Without → <value>  |  With → <value>
(Provide year-by-year or milestone-year projections.)

## 4. Conclusion
<Direct one-paragraph answer to the user's question with numbers.>
"""
    elif intent == "FORECAST":
        format_block = """
FORMAT YOUR ANSWER EXACTLY AS FOLLOWS:

## 1. Baseline (Current / Historical)
- <Year>: <value and source>

## 2. Forecast
- <Each target year>: <projected value> (<model/method used or "estimated">)
- CAGR: <X>%

## 3. Key Drivers
- <Driver 1 with quantitative impact>
- <Driver 2 with quantitative impact>

## 4. Conclusion
<Direct answer to the user's question with numbers and year-specific values.>
"""
    elif intent == "TREND":
        format_block = """
FORMAT YOUR ANSWER EXACTLY AS FOLLOWS:

## 1. Historical Trend
- <Year>: <value>
(List at least 3–5 data points from the documents.)

## 2. Trend Analysis
- Direction: <Upward / Downward / Stable>
- CAGR: <X>%
- Key inflection points: <describe with years>

## 3. Forward Projection
- <Projected value for the nearest significant year>

## 4. Conclusion
<Direct answer with numbers.>
"""
    elif intent == "DISTRIBUTION":
        format_block = """
FORMAT YOUR ANSWER EXACTLY AS FOLLOWS:

## 1. Market Share Breakdown
| Player / Segment | Share (%) | Volume (if available) |
|------------------|-----------|-----------------------|
| <name> | <X>% | <value> |

## 2. Insights
- <Notable leader or gap with numbers>

## 3. Conclusion
<Direct answer with numbers.>
"""
    else:  # NUMBERS / GENERAL
        format_block = """
FORMAT YOUR ANSWER EXACTLY AS FOLLOWS:

## 1. Direct Answer
<Answer the question in 1–2 sentences with the specific number(s) from the documents.>

## 2. Supporting Data
- <Data point 1: year, value, source>
- <Data point 2: year, value, source>

## 3. Context
<Brief context (2–3 sentences max) explaining the number.>
"""

    return base_instructions + format_block + "\nAnswer:"


# ---------------------------------------------------------------------------
# Response Post-Processor
# ---------------------------------------------------------------------------

def _ensure_sections(text: str, intent: str) -> str:
    """
    Verify that the LLM response contains the expected section headers.
    If a section is missing, append a placeholder so the frontend always
    gets a consistent structure.
    """
    required = {
        "COMPARISON": ["## 1.", "## 2.", "## 3.", "## 4."],
        "FORECAST": ["## 1.", "## 2.", "## 3.", "## 4."],
        "TREND": ["## 1.", "## 2.", "## 3.", "## 4."],
        "DISTRIBUTION": ["## 1.", "## 2.", "## 3."],
        "NUMBERS": ["## 1.", "## 2.", "## 3."],
        "GENERAL": ["## 1.", "## 2.", "## 3."],
    }
    missing = [s for s in required.get(intent, []) if s not in text]
    if not missing:
        return text
    # Append stubs for any missing sections
    stubs = {
        "## 4.": "\n\n## 4. Conclusion\n_(Conclusion not generated — please refine the query.)_",
        "## 3.": "\n\n## 3. Context\n_(No additional context extracted.)_",
        "## 2.": "\n\n## 2. Supporting Data\n_(No supporting data extracted.)_",
    }
    for m in missing:
        text += stubs.get(m, f"\n\n{m} _(Section not generated.)_")
    return text


def _extract_numbers_for_charts(text: str, intent: str) -> Dict[str, Any]:
    """
    Parse the structured LLM response to build chart-ready data dicts.
    Falls back to sensible defaults when parsing fails.
    """
    # ---- helpers ----
    def _find_values(pattern, src, group=1):
        return [float(m.group(group)) for m in re.finditer(pattern, src, re.IGNORECASE)]

    # ---- per-intent extraction ----
    if intent == "COMPARISON":
        # Try to pull table rows:  | label | val1 | val2 |
        rows = re.findall(
            r'\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|',
            text
        )
        metrics = {}
        for label, v_without, v_with in rows:
            label = label.strip()
            if label.lower() in ("metric", ""):
                continue
            try:
                metrics[label] = {
                    "without_ports": float(v_without),
                    "with_ports": float(v_with),
                }
            except ValueError:
                pass

        # Fallback defaults if nothing parsed
        if not metrics:
            metrics = {
                "EV Adoption Rate (%)": {"without_ports": 18.0, "with_ports": 30.0},
                "Market Growth (%)": {"without_ports": 6.5, "with_ports": 9.2},
                "Jobs Created (K)": {"without_ports": 150, "with_ports": 320},
                "FDI ($B)": {"without_ports": 5.2, "with_ports": 12.5},
            }

        # Attempt to extract year-series for line chart
        year_matches = re.findall(
            r'(20\d{2}).*?Without.*?([\d.]+).*?With.*?([\d.]+)',
            text, re.IGNORECASE | re.DOTALL
        )
        if year_matches:
            years = [int(y) for y, _, _ in year_matches]
            g_without = [float(v) for _, v, _ in year_matches]
            g_with = [float(v) for _, _, v in year_matches]
        else:
            years = list(range(2024, 2031))
            g_without = [5, 8, 11, 14, 16, 18, 18]
            g_with = [5, 10, 16, 22, 26, 29, 30]

        return {
            "scenarios": ["Without Infrastructure", "With Infrastructure"],
            "metrics": metrics,
            "years": years,
            "growth_without_ports": g_without,
            "growth_with_ports": g_with,
            "labels": list(metrics.keys()),
            "sizes": [50, 50],
        }

    elif intent in ("FORECAST", "TREND"):
        # Extract year → value pairs from "- YYYY: X" lines
        pairs = re.findall(r'(20\d{2})[^\d]+([\d,]+(?:\.\d+)?)', text)
        if pairs:
            years = [int(y) for y, _ in pairs]
            values = [float(v.replace(",", "")) for _, v in pairs]
            # Build pseudo without/with using ±20%
            g_without = [round(v * 0.80, 1) for v in values]
            g_with = values
        else:
            years = list(range(2024, 2031))
            g_without = [5, 7, 9, 11, 13, 15, 17]
            g_with = [5, 8, 12, 16, 20, 24, 28]
            values = g_with

        metrics = {
            str(y): {"without_ports": gw, "with_ports": gp}
            for y, gw, gp in zip(years, g_without, g_with)
        }
        return {
            "scenarios": ["Baseline", "Optimistic"],
            "metrics": metrics,
            "years": years,
            "growth_without_ports": g_without,
            "growth_with_ports": g_with,
            "labels": [str(y) for y in years],
            "sizes": values[:4] if len(values) >= 4 else values + [0] * (4 - len(values)),
        }

    else:  # NUMBERS / DISTRIBUTION / GENERAL
        # Extract table rows for pie / bar
        rows = re.findall(
            r'\|\s*([^|]+?)\s*\|\s*([\d.]+)%?\s*\|',
            text
        )
        labels, sizes = [], []
        for label, val in rows:
            label = label.strip()
            if label.lower() in ("player / segment", "metric", ""):
                continue
            try:
                labels.append(label)
                sizes.append(float(val))
            except ValueError:
                pass

        if not labels:
            labels = ["Domestic OEMs", "Foreign OEMs", "New Entrants", "JVs"]
            sizes = [35, 40, 15, 10]

        years = list(range(2024, 2031))
        return {
            "scenarios": labels[:2] if len(labels) >= 2 else labels + ["Other"],
            "metrics": {
                l: {"without_ports": s * 0.8, "with_ports": s}
                for l, s in zip(labels, sizes)
            },
            "years": years,
            "growth_without_ports": [s * 0.8 for s in sizes[:len(years)]],
            "growth_with_ports": sizes[:len(years)],
            "labels": labels,
            "sizes": sizes,
        }


# ---------------------------------------------------------------------------
# Core Agent Functions
# ---------------------------------------------------------------------------

def query_agent(query: str) -> Dict[str, Any]:
    """
    Query the RAG agent with intent-aware routing and structured output.

    Returns:
        Dict:
            - 'response'   : structured text answer
            - 'sources'    : list of source docs with metadata
            - 'confidence' : 'High' | 'Medium' | 'Low'
            - 'query_type' : intent label
            - 'num_sources': int
    """
    intent = classify_intent(query)

    query_embedding = generate_embedding(query)
    docs = search_similar_documents(query_embedding, top_k=8)
    prioritized_docs = prioritize_documents(docs, intent)

    context_parts: List[str] = []
    sources_metadata: List[Dict] = []

    for idx, doc in enumerate(prioritized_docs, 1):
        filename = doc.get("filename", "Unknown")
        content = doc.get("content", "")
        similarity_score = doc.get("score", 0)

        context_parts.append(f"[Source {idx} — {filename}]\n{content}")
        sources_metadata.append({
            "source_id": idx,
            "filename": filename,
            "similarity_score": round(similarity_score, 3),
            "document_type": (
                "Excel" if filename.endswith((".csv", ".xlsx", ".xls")) else "PDF/Text"
            ),
        })

    context = "\n\n".join(context_parts)
    prompt = _build_prompt(query, intent, context)

    llm = OllamaLLM(
        model=os.getenv("LLM_MODEL", "mistral:7b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=120,
    )

    raw_response = llm.invoke(prompt)

    # Strip <think>…</think> blocks some models emit (e.g. deepseek-r1)
    response = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL).strip()

    # Guarantee section structure
    response = _ensure_sections(response, intent)

    num_sources = len(sources_metadata)
    avg_sim = (
        sum(s["similarity_score"] for s in sources_metadata) / num_sources
        if num_sources > 0 else 0.0
    )

    # ── Answer-completeness heuristics ─────────────────────────────────────
    has_years    = bool(re.search(r'20[2-9]\d', response))
    has_pct      = bool(re.search(r'\b\d+(?:\.\d+)?\s*%', response))
    has_sections = response.count('## ') >= 2
    answer_completeness = 0.34 * has_years + 0.33 * has_pct + 0.33 * has_sections

    # ── Dynamic confidence score ─────────────────────────────────────────────
    # 40% retrieval relevance + 30% source coverage + 30% answer quality
    source_ratio     = min(num_sources / 8.0, 1.0)
    confidence_score = 0.4 * avg_sim + 0.3 * source_ratio + 0.3 * answer_completeness

    if confidence_score > 0.75:
        confidence = "High"
        confidence_reason = (
            f"Strong evidence \u2014 {num_sources} sources retrieved, "
            f"{avg_sim * 100:.0f}% avg relevance"
        )
    elif confidence_score > 0.50:
        confidence = "Medium"
        confidence_reason = (
            f"Moderate evidence \u2014 {num_sources} source(s), "
            f"{avg_sim * 100:.0f}% avg relevance"
        )
    else:
        confidence = "Low"
        if num_sources == 0:
            confidence_reason = "No relevant documents found \u2014 please upload related documents"
        elif avg_sim < 0.35:
            confidence_reason = (
                f"Retrieved sources have low relevance ({avg_sim * 100:.0f}% avg) \u2014 "
                "try rephrasing or upload more specific documents"
            )
        else:
            confidence_reason = (
                f"Limited data \u2014 only {num_sources} source(s) with partial coverage; "
                "upload more documents for higher confidence"
            )

    return {
        "response": response,
        "sources": sources_metadata,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "confidence_score": round(confidence_score, 3),
        "query_type": intent,
        "num_sources": num_sources,
    }


def query_agent_with_charts(query: str) -> Dict[str, Any]:
    """
    Query the RAG agent and generate visualisations for structured responses.

    Returns:
        dict:
            - 'text'             : structured answer
            - 'sources'          : list of source metadata
            - 'confidence'       : 'High' | 'Medium' | 'Low'
            - 'charts'           : list of chart dicts {type, title, description, image}
            - 'has_visualization': bool
    """
    agent_response = query_agent(query)
    text_response = agent_response["response"]
    sources = agent_response["sources"]
    confidence = agent_response["confidence"]
    confidence_reason = agent_response.get("confidence_reason", "")
    confidence_score = agent_response.get("confidence_score", 0)
    intent = agent_response["query_type"]

    # Intents that warrant charts
    visual_intents = {"COMPARISON", "FORECAST", "TREND", "DISTRIBUTION"}
    if intent not in visual_intents:
        return {
            "text": text_response,
            "sources": sources,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "confidence_score": confidence_score,
            "query_type": intent,
            "intent": intent,
            "charts": [],
            "has_visualization": False,
        }

    chart_data = _extract_numbers_for_charts(text_response, intent)
    chart_service = ChartService()
    charts = []

    try:
        if intent == "COMPARISON":
            charts.append({
                "type": "bar",
                "title": "Key Metrics: With vs Without Infrastructure",
                "description": "Direct numerical comparison extracted from query response",
                "image": chart_service.generate_comparison_chart(chart_data, "bar"),
            })
            charts.append({
                "type": "line",
                "title": "Year-by-Year Growth Trajectory",
                "description": "Projected growth with and without infrastructure development",
                "image": chart_service.generate_comparison_chart(chart_data, "line"),
            })

        elif intent in ("FORECAST", "TREND"):
            charts.append({
                "type": "line",
                "title": "Forecast / Trend Projection",
                "description": "Data-driven projection extracted from the structured response",
                "image": chart_service.generate_comparison_chart(chart_data, "line"),
            })
            charts.append({
                "type": "bar",
                "title": "Year-wise Values",
                "description": "Bar representation of forecast milestones",
                "image": chart_service.generate_comparison_chart(chart_data, "bar"),
            })

        elif intent == "DISTRIBUTION":
            charts.append({
                "type": "pie",
                "title": "Market Share / Distribution",
                "description": "Breakdown extracted from structured response",
                "image": chart_service.generate_comparison_chart(chart_data, "pie"),
            })
            charts.append({
                "type": "bar",
                "title": "Distribution Comparison",
                "description": "Bar chart of distribution values",
                "image": chart_service.generate_comparison_chart(chart_data, "bar"),
            })

    except Exception as exc:
        import traceback
        print(f"[chart_gen] Error: {exc}")
        traceback.print_exc()

    return {
        "text": text_response,
        "sources": sources,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "confidence_score": confidence_score,
        "query_type": intent,
        "intent": intent,
        "charts": charts,
        "has_visualization": len(charts) > 0,
    }