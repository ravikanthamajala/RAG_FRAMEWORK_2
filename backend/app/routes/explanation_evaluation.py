from flask import Blueprint, jsonify, request

from evaluation.explanation_grounding_evaluation import evaluate_explanation_grounding

explanation_evaluation_bp = Blueprint("explanation_evaluation", __name__)


@explanation_evaluation_bp.route("/evaluate", methods=["POST"])
def evaluate_grounding_quality():
    payload = request.get_json(silent=True) or {}
    records = payload.get("records") or payload.get("explanations") or []

    if not isinstance(records, list) or not records:
        return jsonify({
            "error": "Provide a non-empty 'records' array containing explanation/context items."
        }), 400

    evaluation = evaluate_explanation_grounding(records)
    details_df = evaluation["details"]
    summary_df = evaluation["summary"]

    return jsonify({
        "num_records": int(len(details_df)),
        "details_table": details_df.to_dict(orient="records"),
        "summary_table": summary_df.round(4).to_dict(orient="records"),
    }), 200
