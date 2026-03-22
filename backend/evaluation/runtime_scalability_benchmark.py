import argparse
import json
import threading
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import psutil
from statsmodels.tools.sm_exceptions import ConvergenceWarning
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

PROPHET_AVAILABLE = False
warnings.filterwarnings("ignore", category=ConvergenceWarning)

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False


@dataclass
class BenchmarkConfig:
    input_csv: Path
    output_dir: Path
    target_col: str = "EV_Sales_Quantity"
    repeats: int = 5
    sizes: Tuple[int, ...] = (10_000, 50_000, 100_000)
    inference_batch_size: int = 128
    random_seed: int = 42


def get_dataset_label(size: int) -> str:
    mapping = {
        10_000: "Small (10k)",
        50_000: "Medium (50k)",
        100_000: "Large (100k)",
    }
    return mapping.get(size, f"{size} rows")


class PeakMemoryMonitor:
    def __init__(self, interval_seconds: float = 0.02):
        self.interval_seconds = interval_seconds
        self._process = psutil.Process()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._peak_rss_bytes = 0

    def _loop(self):
        while self._running:
            rss = self._process.memory_info().rss
            if rss > self._peak_rss_bytes:
                self._peak_rss_bytes = rss
            time.sleep(self.interval_seconds)

    def start(self):
        self._peak_rss_bytes = self._process.memory_info().rss
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
        return self._peak_rss_bytes / (1024 * 1024)


def set_seed(seed: int):
    np.random.seed(seed)


def load_base_series(input_csv: Path, target_col: str) -> np.ndarray:
    df = pd.read_csv(input_csv)
    if target_col not in df.columns:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            raise ValueError(f"No numeric target column found in {input_csv}")
        target_col = numeric_cols[0]

    series = pd.to_numeric(df[target_col], errors="coerce").dropna().to_numpy(dtype=float)
    series = series[series >= 0]
    if len(series) < 200:
        raise ValueError("Input data too small for benchmarking (need >= 200 points)")
    return series


def make_series_for_size(base_series: np.ndarray, size: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if len(base_series) >= size:
        start = int(rng.integers(0, len(base_series) - size + 1))
        y = base_series[start:start + size].copy()
    else:
        reps = int(np.ceil(size / len(base_series)))
        y = np.tile(base_series, reps)[:size].copy()

    trend = np.linspace(0, np.std(y) * 0.05, size)
    jitter = rng.normal(0, np.std(y) * 0.01 + 1e-9, size)
    y = np.maximum(0, y + trend + jitter)
    return y


def make_datetime_index(length: int) -> pd.DataFrame:
    return pd.DataFrame({
        "ds": pd.date_range(start="2010-01-01", periods=length, freq="D")
    })


def make_xgb_supervised(y: np.ndarray, lags: int = 12) -> Tuple[np.ndarray, np.ndarray]:
    rows = len(y) - lags
    x = np.zeros((rows, lags), dtype=float)
    target = np.zeros(rows, dtype=float)
    for i in range(lags, len(y)):
        x[i - lags] = y[i - lags:i]
        target[i - lags] = y[i]
    return x, target


def benchmark_model(
    train_fn: Callable[[], object],
    infer_fn: Callable[[object], None],
) -> Tuple[float, float, float]:
    monitor = PeakMemoryMonitor(interval_seconds=0.02)
    t0 = time.perf_counter()
    monitor.start()
    model_obj = train_fn()
    peak_memory_mb = monitor.stop()
    train_time_s = time.perf_counter() - t0

    t1 = time.perf_counter()
    infer_fn(model_obj)
    inference_ms = (time.perf_counter() - t1) * 1000.0

    return train_time_s, inference_ms, peak_memory_mb


def run_repeated_experiment(
    train_fn_factory: Callable[[int], Tuple[Callable[[], object], Callable[[object], None]]],
    repeats: int,
    seed_base: int,
) -> Tuple[List[float], List[float], List[float], List[Dict]]:
    train_times: List[float] = []
    infer_times: List[float] = []
    peak_memories: List[float] = []
    details: List[Dict] = []

    for run_idx in range(repeats):
        run_seed = seed_base + run_idx
        set_seed(run_seed)
        try:
            train_fn, infer_fn = train_fn_factory(run_seed)
            train_s, infer_ms, peak_mb = benchmark_model(train_fn, infer_fn)
            train_times.append(train_s)
            infer_times.append(infer_ms)
            peak_memories.append(peak_mb)
            details.append({
                "run": run_idx + 1,
                "seed": run_seed,
                "training_time_s": train_s,
                "inference_time_ms_per_batch": infer_ms,
                "peak_memory_mb": peak_mb,
                "status": "ok",
            })
        except Exception as exc:
            details.append({
                "run": run_idx + 1,
                "seed": run_seed,
                "training_time_s": np.nan,
                "inference_time_ms_per_batch": np.nan,
                "peak_memory_mb": np.nan,
                "status": f"failed: {type(exc).__name__}: {exc}",
            })

    return train_times, infer_times, peak_memories, details


def build_arima_benchmark(y: np.ndarray, batch_size: int):
    def train_fn():
        model = ARIMA(y, order=(1, 1, 1))
        return model.fit(method_kwargs={"maxiter": 25})

    def infer_fn(fitted):
        fitted.forecast(steps=batch_size)

    return train_fn, infer_fn


def build_sarima_benchmark(y: np.ndarray, batch_size: int):
    def train_fn():
        model = SARIMAX(
            y,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            simple_differencing=True,
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        return model.fit(disp=False, maxiter=20)

    def infer_fn(fitted):
        fitted.forecast(steps=batch_size)

    return train_fn, infer_fn


def build_additive_benchmark(y: np.ndarray, batch_size: int):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    def train_fn():
        model = ExponentialSmoothing(y, trend="add", seasonal="add", seasonal_periods=12)
        return model.fit(optimized=True)

    def infer_fn(fitted):
        fitted.forecast(batch_size)

    return train_fn, infer_fn, "Additive(ETS)"


def build_xgb_benchmark(y: np.ndarray, batch_size: int, seed: int):
    if not XGB_AVAILABLE:
        raise ImportError("xgboost is not installed")

    x_train, y_train = make_xgb_supervised(y, lags=12)
    infer_seed = y[-12:].copy()

    def train_fn():
        model = XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=seed,
        )
        model.fit(x_train, y_train)
        return model

    def infer_fn(model):
        history = list(infer_seed)
        for _ in range(batch_size):
            x = np.asarray(history[-12:]).reshape(1, -1)
            p = float(model.predict(x)[0])
            history.append(max(0.0, p))

    return train_fn, infer_fn


def format_table(df: pd.DataFrame) -> str:
    lines = []
    lines.append("Dataset | Model | Training Time (s) | Inference Time (ms/batch) | Peak Memory (MB)")
    lines.append("---|---|---:|---:|---:")
    for _, row in df.iterrows():
        lines.append(
            f"{row['Dataset']} | {row['Model']} | {row['Training Time (s)']:.3f} | "
            f"{row['Inference Time (ms/batch)']:.3f} | {row['Peak Memory (MB)']:.2f}"
        )
    return "\n".join(lines)


def format_latex(df: pd.DataFrame) -> str:
    latex = []
    latex.append("\\begin{table}[h]")
    latex.append("\\centering")
    latex.append("\\caption{Runtime Scalability Metrics (Average of 5 Runs)}")
    latex.append("\\label{tab:runtime_scalability}")
    latex.append("\\begin{tabular}{l l c c c}")
    latex.append("\\hline")
    latex.append("Dataset & Model & Train Time (s) & Infer Time (ms) & Peak Memory (MB) \\")
    latex.append("\\hline")
    for _, row in df.iterrows():
        latex.append(
            f"{row['Dataset']} & {row['Model']} & {row['Training Time (s)']:.3f} & "
            f"{row['Inference Time (ms/batch)']:.3f} & {row['Peak Memory (MB)']:.2f} \\")
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")
    return "\n".join(latex)


def format_ieee_dataset_only(df: pd.DataFrame) -> str:
    lines = []
    lines.append("Dataset | Training Time | Inference Time | Memory Usage")
    lines.append("---|---:|---:|---:")
    for _, row in df.iterrows():
        dataset_model = f"{row['Dataset']} - {row['Model']}"
        lines.append(
            f"{dataset_model} | {row['Training Time (s)']:.3f} s | "
            f"{row['Inference Time (ms/batch)']:.3f} ms | {row['Peak Memory (MB)']:.2f} MB"
        )
    return "\n".join(lines)


def build_framework_summary(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return pd.DataFrame(
            columns=[
                "Dataset Size",
                "Training Time (seconds)",
                "Inference Time (milliseconds)",
                "Memory Usage (MB)",
            ]
        )

    framework_df = (
        summary_df.groupby(["Dataset", "Rows"], as_index=False)
        .agg(
            **{
                "Training Time (seconds)": ("Training Time (s)", "sum"),
                "Inference Time (milliseconds)": ("Inference Time (ms/batch)", "sum"),
                "Memory Usage (MB)": ("Peak Memory (MB)", "max"),
            }
        )
        .rename(columns={"Dataset": "Dataset Size"})
        .sort_values("Rows")
        .reset_index(drop=True)
    )
    return framework_df[[
        "Dataset Size",
        "Training Time (seconds)",
        "Inference Time (milliseconds)",
        "Memory Usage (MB)",
    ]]


def format_framework_table(df: pd.DataFrame) -> str:
    lines = []
    lines.append("Dataset Size | Training Time (seconds) | Inference Time (milliseconds) | Memory Usage (MB)")
    lines.append("---|---:|---:|---:")
    for _, row in df.iterrows():
        lines.append(
            f"{row['Dataset Size']} | {row['Training Time (seconds)']:.3f} | "
            f"{row['Inference Time (milliseconds)']:.3f} | {row['Memory Usage (MB)']:.2f}"
        )
    return "\n".join(lines)


def run_benchmark(cfg: BenchmarkConfig):
    set_seed(cfg.random_seed)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    base_series = load_base_series(cfg.input_csv, cfg.target_col)

    records: List[Dict] = []
    details: List[Dict] = []

    for size in cfg.sizes:
        dataset_label = get_dataset_label(size)
        y = make_series_for_size(base_series, size=size, seed=cfg.random_seed + size)

        models = ["ARIMA", "SARIMA", "Additive", "XGBoost"]
        for model_name in models:
            effective_model_name = model_name

            if model_name == "ARIMA":
                train_fn_factory = lambda _seed: build_arima_benchmark(y, cfg.inference_batch_size)
            elif model_name == "SARIMA":
                train_fn_factory = lambda _seed: build_sarima_benchmark(y, cfg.inference_batch_size)
            elif model_name == "Additive":
                train_fn, infer_fn, effective_model_name = build_additive_benchmark(y, cfg.inference_batch_size)
                train_fn_factory = lambda _seed, tr=train_fn, inf=infer_fn: (tr, inf)
            elif model_name == "XGBoost":
                if not XGB_AVAILABLE:
                    continue
                train_fn_factory = lambda seed: build_xgb_benchmark(y, cfg.inference_batch_size, seed=seed)
            else:
                continue

            train_times, infer_times, peak_memories, run_details = run_repeated_experiment(
                train_fn_factory=train_fn_factory,
                repeats=cfg.repeats,
                seed_base=cfg.random_seed + size,
            )

            for run_result in run_details:
                details.append({
                    "Dataset": dataset_label,
                    "Rows": size,
                    "Model": effective_model_name,
                    "Run": run_result["run"],
                    "Training Time (s)": run_result["training_time_s"],
                    "Inference Time (ms/batch)": run_result["inference_time_ms_per_batch"],
                    "Peak Memory (MB)": run_result["peak_memory_mb"],
                    "Status": run_result["status"],
                })

            if train_times:
                records.append({
                    "Dataset": dataset_label,
                    "Rows": size,
                    "Model": effective_model_name,
                    "Training Time (s)": float(np.mean(train_times)),
                    "Inference Time (ms/batch)": float(np.mean(infer_times)),
                    "Peak Memory (MB)": float(np.mean(peak_memories)),
                })

    summary_df = pd.DataFrame(records).sort_values(["Rows", "Model"]).reset_index(drop=True)
    details_df = pd.DataFrame(details).sort_values(["Rows", "Model", "Run"]).reset_index(drop=True)

    summary_csv = cfg.output_dir / "runtime_scalability_summary.csv"
    runs_csv = cfg.output_dir / "runtime_scalability_runs.csv"
    framework_csv = cfg.output_dir / "runtime_framework_performance_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    details_df.to_csv(runs_csv, index=False)

    framework_df = build_framework_summary(summary_df)
    framework_df.to_csv(framework_csv, index=False)

    markdown_table = format_table(summary_df)
    latex_table = format_latex(summary_df)
    ieee_dataset_table = format_ieee_dataset_only(summary_df)
    framework_markdown_table = format_framework_table(framework_df)

    (cfg.output_dir / "runtime_scalability_table.md").write_text(markdown_table, encoding="utf-8")
    (cfg.output_dir / "runtime_scalability_table.tex").write_text(latex_table, encoding="utf-8")
    (cfg.output_dir / "runtime_scalability_dataset_table.md").write_text(
        ieee_dataset_table,
        encoding="utf-8",
    )
    (cfg.output_dir / "runtime_framework_performance_table.md").write_text(
        framework_markdown_table,
        encoding="utf-8",
    )

    metadata = {
        "input_csv": str(cfg.input_csv),
        "target_col": cfg.target_col,
        "repeats": cfg.repeats,
        "sizes": list(cfg.sizes),
        "inference_batch_size": cfg.inference_batch_size,
        "prophet_available": PROPHET_AVAILABLE,
        "xgboost_available": XGB_AVAILABLE,
    }
    (cfg.output_dir / "runtime_scalability_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("\n=== TABLE-READY RESULTS ===")
    print(markdown_table)
    print("\n=== DATASET-ONLY TABLE FORMAT ===")
    print(ieee_dataset_table)
    print("\n=== FRAMEWORK PERFORMANCE TABLE ===")
    print(framework_markdown_table)
    print("\nSaved files:")
    print(summary_csv)
    print(runs_csv)
    print(framework_csv)
    print(cfg.output_dir / "runtime_scalability_table.md")
    print(cfg.output_dir / "runtime_scalability_table.tex")
    print(cfg.output_dir / "runtime_scalability_dataset_table.md")
    print(cfg.output_dir / "runtime_framework_performance_table.md")


def parse_args():
    parser = argparse.ArgumentParser(description="Runtime scalability benchmark for forecasting models")
    parser.add_argument(
        "--input-csv",
        type=str,
        default="backend/uploads/EV_Dataset.csv",
        help="Path to source CSV",
    )
    parser.add_argument(
        "--target-col",
        type=str,
        default="EV_Sales_Quantity",
        help="Target column for univariate series",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help="Number of experiment repetitions",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backend/evaluation/outputs",
        help="Directory for results",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    config = BenchmarkConfig(
        input_csv=Path(args.input_csv),
        output_dir=Path(args.output_dir),
        target_col=args.target_col,
        repeats=args.repeats,
    )
    run_benchmark(config)