"""
Metrics collection for research paper evaluation.
Tracks RAG performance, query accuracy, and system performance.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class MetricsCollector:
    """Collects evaluation metrics for the RAG system and forecasting models."""

    def __init__(self, log_directory: str = "logs/metrics") -> None:
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        self.metrics: List[Dict[str, Any]] = []

    def log_query_performance(
        self,
        query: str,
        response: str,
        retrieval_time: float,
        generation_time: float,
        documents_retrieved: int,
        agent_actions: List[str],
    ) -> None:
        """Log RAG query performance metrics."""
        metric = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response_length": len(response),
            "retrieval_time_ms": retrieval_time * 1000.0,
            "generation_time_ms": generation_time * 1000.0,
            "total_time_ms": (retrieval_time + generation_time) * 1000.0,
            "documents_retrieved": documents_retrieved,
            "agent_actions_count": len(agent_actions),
            "agent_actions": agent_actions,
        }
        self.metrics.append(metric)
        self._save_metrics()

    def log_forecast_accuracy(
        self,
        actual_values: List[float],
        predicted_values: List[float],
        model_name: str,
    ) -> Dict[str, float]:
        """Log forecasting model accuracy metrics."""
        try:
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        except Exception as exc:  # pragma: no cover - optional dependency
            raise ImportError("scikit-learn is required for forecasting metrics") from exc

        mae = mean_absolute_error(actual_values, predicted_values)
        rmse = mean_squared_error(actual_values, predicted_values) ** 0.5
        r2 = r2_score(actual_values, predicted_values)

        metric = {
            "timestamp": datetime.now().isoformat(),
            "model_name": model_name,
            "mae": float(mae),
            "rmse": float(rmse),
            "r2_score": float(r2),
            "samples": len(actual_values),
        }
        self.metrics.append(metric)
        self._save_metrics()

        return {"mae": float(mae), "rmse": float(rmse), "r2": float(r2)}

    def _save_metrics(self) -> None:
        """Save metrics to a JSON file."""
        filename = self.log_directory / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(self.metrics, handle, indent=2)


# Global metrics collector
metrics_collector = MetricsCollector()
