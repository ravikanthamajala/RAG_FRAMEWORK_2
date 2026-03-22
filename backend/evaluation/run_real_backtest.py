import argparse
import json
import logging
import os
import platform
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from forecast_visualization import generate_forecast_visualizations

from app.services.forecast_preprocessing import ForecastPreprocessingPipeline, PreprocessingConfig

try:
    from xgboost import XGBRegressor
except Exception:
    XGBRegressor = None

try:
    import yaml
except Exception:
    yaml = None


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def mae(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.mean(np.abs(y - yhat)))


def rmse(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def mape(y: np.ndarray, yhat: np.ndarray, eps: float = 1e-8) -> float:
    y = np.asarray(y, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    return float(np.mean(np.abs((y - yhat) / np.maximum(np.abs(y), eps))) * 100.0)


@dataclass
class Config:
    experiment_name: str = "forecast_backtest"
    results_root: str = "backend/evaluation/results"
    run_id: str = ""
    config_path: str = ""
    data_csv: str = "backend/uploads/EV_Dataset.csv"
    date_col: str = "Date"
    target_col: str = "EV_Sales_Quantity"
    monthly_freq: str = "MS"
    monthly_aggregation: str = "sum"
    interpolation_method: str = "linear"
    outlier_method: str = "iqr"
    outlier_action: str = "interpolate"
    zscore_threshold: float = 3.0
    iqr_multiplier: float = 1.5
    horizons: Tuple[int, ...] = (1, 3, 6, 12)
    initial_train_ratio: float = 0.6
    min_train_points: int = 24
    origin_step: int = 1
    max_lag: int = 12
    lag_steps: Tuple[int, ...] = (1, 3, 6, 12)
    seasonal_period: int = 12
    use_log1p: bool = True
    random_seed: int = 42
    rolling_windows: Tuple[int, ...] = (3, 6, 12)
    policy_events: Tuple[Tuple[str, float], ...] = tuple()
    interval_alpha: float = 0.05
    n_bootstrap_samples: int = 1000
    dm_alpha: float = 0.05
    output_dir: str = "backend/evaluation/outputs"


def _resolve_path(path_value: str, prefer_project_root: bool = True) -> str:
    if not path_value:
        return path_value
    if os.path.isabs(path_value):
        return path_value
    candidates = []
    if prefer_project_root:
        candidates.append(os.path.join(PROJECT_ROOT, path_value))
    candidates.extend(
        [
            path_value,
            os.path.join(BACKEND_DIR, path_value),
            os.path.join(CURRENT_DIR, path_value),
        ]
    )
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return candidates[0]


def _normalize_policy_events(raw_policy_events: Any) -> Tuple[Tuple[str, float], ...]:
    if raw_policy_events is None:
        return tuple()
    normalized = []
    for item in raw_policy_events:
        if isinstance(item, dict):
            event_date = item.get("date")
            intensity = item.get("intensity", 0.0)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            event_date, intensity = item[0], item[1]
        else:
            continue
        normalized.append((str(event_date), float(intensity)))
    return tuple(normalized)


def _coerce_sequence(value: Any) -> Tuple[int, ...]:
    if isinstance(value, tuple):
        return tuple(int(v) for v in value)
    if isinstance(value, list):
        return tuple(int(v) for v in value)
    return value


def _config_to_serializable_dict(cfg: Config) -> Dict[str, Any]:
    data = asdict(cfg)
    data["horizons"] = [int(v) for v in cfg.horizons]
    data["lag_steps"] = [int(v) for v in cfg.lag_steps]
    data["rolling_windows"] = [int(v) for v in cfg.rolling_windows]
    data["policy_events"] = [
        {"date": event_date, "intensity": float(intensity)} for event_date, intensity in cfg.policy_events
    ]
    return data


def load_experiment_config(config_path: str) -> Config:
    resolved_path = _resolve_path(config_path, prefer_project_root=True)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    suffix = os.path.splitext(resolved_path)[1].lower()
    with open(resolved_path, "r", encoding="utf-8") as f:
        if suffix in {".yaml", ".yml"}:
            if yaml is None:
                raise ImportError("PyYAML is required to load YAML experiment configs.")
            raw = yaml.safe_load(f) or {}
        else:
            raw = json.load(f)

    raw = dict(raw)
    raw["config_path"] = resolved_path
    raw["policy_events"] = _normalize_policy_events(raw.get("policy_events"))
    for key in ["horizons", "lag_steps", "rolling_windows"]:
        if key in raw:
            raw[key] = _coerce_sequence(raw[key])
    if "data_csv" in raw:
        raw["data_csv"] = _resolve_path(raw["data_csv"], prefer_project_root=True)
    if "results_root" in raw:
        raw["results_root"] = _resolve_path(raw["results_root"], prefer_project_root=True)
    if "output_dir" in raw and raw["output_dir"]:
        raw["output_dir"] = _resolve_path(raw["output_dir"], prefer_project_root=True)
    return Config(**raw)


def prepare_experiment_output_dir(cfg: Config) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = cfg.run_id or timestamp
    results_root = _resolve_path(cfg.results_root, prefer_project_root=True)
    output_dir = cfg.output_dir
    if output_dir and output_dir != "backend/evaluation/outputs":
        output_dir = _resolve_path(output_dir, prefer_project_root=True)
    else:
        output_dir = os.path.join(results_root, cfg.experiment_name, run_id)
    os.makedirs(output_dir, exist_ok=True)
    cfg.run_id = run_id
    cfg.results_root = results_root
    cfg.output_dir = output_dir
    return output_dir


def setup_experiment_logger(output_dir: str, experiment_name: str) -> str:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    log_path = os.path.join(output_dir, "experiment.log")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.info("Initialized experiment logger | experiment=%s | log=%s", experiment_name, log_path)
    return log_path


def build_model_hyperparameters(cfg: Config) -> Dict[str, Dict[str, Any]]:
    return {
        "ARIMA": {
            "order": [1, 1, 1],
            "fallback_order": [1, 1, 0],
        },
        "SARIMA": {
            "order": [1, 1, 1],
            "seasonal_order": [1, 1, 1, int(cfg.seasonal_period)],
        },
        "Additive": {
            "regressor": "LinearRegression",
            "lag_steps": [int(v) for v in cfg.lag_steps],
            "rolling_windows": [int(v) for v in cfg.rolling_windows],
            "feature_scaler": "StandardScaler",
        },
        "XGBoost": {
            "n_estimators": 300,
            "learning_rate": 0.05,
            "max_depth": 4,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "objective": "reg:squarederror",
            "random_state": int(cfg.random_seed),
            "n_jobs": 1,
        },
        "Hybrid": {
            "base_model": "ARIMA/SARIMA",
            "residual_model": "XGBoost" if XGBRegressor is not None else "LinearRegression",
            "residual_xgb_n_estimators": 250,
            "residual_xgb_learning_rate": 0.05,
            "residual_xgb_max_depth": 4,
            "n_bootstrap_samples": int(cfg.n_bootstrap_samples),
            "interval_alpha": float(cfg.interval_alpha),
            "random_state": int(cfg.random_seed),
            "n_jobs": 1,
        },
    }


def save_experiment_manifest(cfg: Config, output_dir: str, log_path: str) -> None:
    manifest = {
        "experiment_name": cfg.experiment_name,
        "run_id": cfg.run_id,
        "config_path": cfg.config_path,
        "output_dir": output_dir,
        "log_path": log_path,
        "config": _config_to_serializable_dict(cfg),
        "model_hyperparameters": build_model_hyperparameters(cfg),
        "seed_control": {
            "python_random": int(cfg.random_seed),
            "numpy_random": int(cfg.random_seed),
            "python_hash_seed": str(cfg.random_seed),
        },
    }
    with open(os.path.join(output_dir, "experiment_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with open(os.path.join(output_dir, "resolved_config.json"), "w", encoding="utf-8") as f:
        json.dump(_config_to_serializable_dict(cfg), f, indent=2)

    with open(os.path.join(output_dir, "model_hyperparameters.json"), "w", encoding="utf-8") as f:
        json.dump(build_model_hyperparameters(cfg), f, indent=2)


def load_series(cfg: Config) -> pd.DataFrame:
    data_csv = cfg.data_csv
    if not os.path.isabs(data_csv):
        candidate_paths = [
            data_csv,
            os.path.join(PROJECT_ROOT, data_csv),
            os.path.join(BACKEND_DIR, data_csv),
            os.path.join(BACKEND_DIR, os.path.basename(data_csv)),
            os.path.join(BACKEND_DIR, "uploads", os.path.basename(data_csv)),
        ]
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                data_csv = candidate
                break
    raw_df = pd.read_csv(data_csv)
    pipeline = ForecastPreprocessingPipeline(
        PreprocessingConfig(
            date_col=cfg.date_col,
            target_col=cfg.target_col,
            monthly_freq=cfg.monthly_freq,
            monthly_aggregation=cfg.monthly_aggregation,
            interpolation_method=cfg.interpolation_method,
            outlier_method=cfg.outlier_method,
            outlier_action=cfg.outlier_action,
            zscore_threshold=cfg.zscore_threshold,
            iqr_multiplier=cfg.iqr_multiplier,
            non_negative_target=True,
            min_train_points=cfg.min_train_points,
            test_ratio=max(0.0, 1.0 - cfg.initial_train_ratio),
        )
    )
    artifacts = pipeline.preprocess_target_series(raw_df)
    logging.info(
        "Preprocessing complete | monthly_rows=%s | outliers_detected=%s | date_range=[%s to %s]",
        int(artifacts.summary.get("monthly_rows", len(artifacts.cleaned_df))),
        int(artifacts.summary.get("outliers_detected", 0)),
        str(artifacts.cleaned_df["ds"].min().date()) if not artifacts.cleaned_df.empty else "N/A",
        str(artifacts.cleaned_df["ds"].max().date()) if not artifacts.cleaned_df.empty else "N/A",
    )
    return artifacts.cleaned_df


def target_transform(y: np.ndarray, use_log1p: bool) -> np.ndarray:
    if use_log1p:
        return np.log1p(np.asarray(y, dtype=float))
    return np.asarray(y, dtype=float)


def target_inverse_transform(y_t: np.ndarray, use_log1p: bool) -> np.ndarray:
    arr = np.asarray(y_t, dtype=float)
    if use_log1p:
        arr = np.expm1(arr)
    return np.maximum(0.0, arr)


FEATURE_COLUMNS: Tuple[str, ...] = (
    "lag_1",
    "lag_3",
    "lag_6",
    "lag_12",
    "rolling_mean_3",
    "rolling_mean_6",
    "rolling_std_6",
    "month",
    "quarter",
    "year",
    "policy_event_flag",
    "policy_intensity_score",
)

EXOGENOUS_FEATURE_COLUMNS: Tuple[str, ...] = (
    "month",
    "quarter",
    "year",
    "policy_event_flag",
    "policy_intensity_score",
)

EXOGENOUS_FEATURE_INDEX = {name: FEATURE_COLUMNS.index(name) for name in EXOGENOUS_FEATURE_COLUMNS}


def _build_policy_map(policy_events: Tuple[Tuple[str, float], ...]) -> Dict[pd.Period, float]:
    policy_map: Dict[pd.Period, float] = {}
    for event_date, intensity in policy_events:
        ts = pd.to_datetime(event_date, errors="coerce")
        if pd.isna(ts):
            continue
        period = ts.to_period("M")
        policy_map[period] = float(intensity)
    return policy_map


def _policy_features(target_date: pd.Timestamp, policy_map: Dict[pd.Period, float]) -> Tuple[float, float]:
    period = pd.Timestamp(target_date).to_period("M")
    intensity = float(policy_map.get(period, 0.0))
    flag = 1.0 if intensity != 0.0 else 0.0
    return flag, intensity


def _inject_exogenous_noise(
    feature_row: np.ndarray,
    noise_level: float,
    rng: np.random.Generator,
) -> np.ndarray:
    if noise_level <= 0:
        return feature_row

    row = feature_row.copy().astype(float)
    for name, idx in EXOGENOUS_FEATURE_INDEX.items():
        base_value = float(row[idx])
        sigma = noise_level * max(abs(base_value), 1.0)
        row[idx] = base_value + float(rng.normal(loc=0.0, scale=sigma))

        if name == "month":
            row[idx] = float(np.clip(row[idx], 1.0, 12.0))
        elif name == "quarter":
            row[idx] = float(np.clip(row[idx], 1.0, 4.0))
        elif name == "year":
            row[idx] = float(max(1900.0, row[idx]))
        elif name == "policy_event_flag":
            row[idx] = float(np.clip(row[idx], 0.0, 1.0))

    return row


def _safe_std(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(np.std(values, ddof=1))


def _required_history(lag_steps: Tuple[int, ...]) -> int:
    return max(max(lag_steps), 6)


def _make_feature_row(
    history: List[float],
    target_date: pd.Timestamp,
    lag_steps: Tuple[int, ...],
    policy_map: Dict[pd.Period, float],
) -> np.ndarray:
    lag_1 = float(history[-1])
    lag_3 = float(history[-3])
    lag_6 = float(history[-6])
    lag_12 = float(history[-12])

    rolling_mean_3 = float(np.mean(history[-3:]))
    rolling_mean_6 = float(np.mean(history[-6:]))
    rolling_std_6 = _safe_std(history[-6:])

    ts = pd.Timestamp(target_date)
    month = float(ts.month)
    quarter = float(ts.quarter)
    year = float(ts.year)

    policy_event_flag, policy_intensity_score = _policy_features(ts, policy_map=policy_map)

    return np.asarray(
        [
            lag_1,
            lag_3,
            lag_6,
            lag_12,
            rolling_mean_3,
            rolling_mean_6,
            rolling_std_6,
            month,
            quarter,
            year,
            policy_event_flag,
            policy_intensity_score,
        ],
        dtype=float,
    )


def build_supervised_matrix(
    series_t: np.ndarray,
    series_dates: pd.Series,
    lag_steps: Tuple[int, ...],
    policy_map: Dict[pd.Period, float],
    noise_level: float = 0.0,
    rng: np.random.Generator = None,
) -> Tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    values = np.asarray(series_t, dtype=float).tolist()
    min_required = _required_history(lag_steps)

    for idx in range(min_required, len(values)):
        history = values[:idx]
        target_date = pd.Timestamp(series_dates.iloc[idx])
        X.append(
            _make_feature_row(
                history,
                target_date=target_date,
                lag_steps=lag_steps,
                policy_map=policy_map,
            )
        )
        y.append(values[idx])

    if len(X) == 0:
        return np.empty((0, len(FEATURE_COLUMNS)), dtype=float), np.empty((0,), dtype=float)

    X_arr = np.asarray(X, dtype=float)
    if noise_level > 0:
        local_rng = rng if rng is not None else np.random.default_rng(42)
        X_arr = np.vstack([_inject_exogenous_noise(row, noise_level=noise_level, rng=local_rng) for row in X_arr])

    return X_arr, np.asarray(y, dtype=float)


def _mean_fallback(train_t: np.ndarray, steps: int) -> np.ndarray:
    if len(train_t) == 0:
        return np.zeros(steps, dtype=float)
    return np.repeat(float(np.mean(train_t)), steps)


def forecast_arima(train_t: np.ndarray, steps: int) -> np.ndarray:
    if len(train_t) < 8:
        return _mean_fallback(train_t, steps)
    try:
        fit = ARIMA(train_t, order=(1, 1, 1)).fit()
        return np.asarray(fit.forecast(steps=steps), dtype=float)
    except Exception:
        return _mean_fallback(train_t, steps)


def forecast_sarima(train_t: np.ndarray, steps: int, seasonal_period: int) -> np.ndarray:
    if len(train_t) < (seasonal_period + 8):
        return _mean_fallback(train_t, steps)
    try:
        fit = ARIMA(train_t, order=(1, 1, 1), seasonal_order=(1, 1, 1, seasonal_period)).fit()
        return np.asarray(fit.forecast(steps=steps), dtype=float)
    except Exception:
        return forecast_arima(train_t, steps)


def forecast_additive_recursive(
    train_t: np.ndarray,
    train_dates: pd.Series,
    steps: int,
    lag_steps: Tuple[int, ...],
    policy_map: Dict[pd.Period, float],
    noise_level: float = 0.0,
    rng: np.random.Generator = None,
) -> np.ndarray:
    min_required = _required_history(lag_steps)
    if len(train_t) <= min_required + 4:
        return _mean_fallback(train_t, steps)

    X_train, y_train = build_supervised_matrix(
        train_t,
        series_dates=train_dates,
        lag_steps=lag_steps,
        policy_map=policy_map,
        noise_level=noise_level,
        rng=rng,
    )
    if len(X_train) == 0:
        return _mean_fallback(train_t, steps)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    model = LinearRegression()
    model.fit(X_scaled, y_train)

    history = np.asarray(train_t, dtype=float).tolist()
    last_train_date = pd.Timestamp(train_dates.iloc[-1])
    preds = []
    for step_idx in range(1, steps + 1):
        target_date = last_train_date + pd.DateOffset(months=step_idx)
        x_next = _make_feature_row(
            history,
            target_date=target_date,
            lag_steps=lag_steps,
            policy_map=policy_map,
        ).reshape(1, -1)
        if noise_level > 0:
            local_rng = rng if rng is not None else np.random.default_rng(42)
            x_next = _inject_exogenous_noise(x_next.flatten(), noise_level=noise_level, rng=local_rng).reshape(1, -1)
        x_next_scaled = scaler.transform(x_next)
        pred = float(model.predict(x_next_scaled)[0])
        preds.append(pred)
        history.append(pred)

    return np.asarray(preds, dtype=float)


def forecast_xgboost_recursive(
    train_t: np.ndarray,
    train_dates: pd.Series,
    steps: int,
    lag_steps: Tuple[int, ...],
    policy_map: Dict[pd.Period, float],
    seed: int,
    noise_level: float = 0.0,
    rng: np.random.Generator = None,
) -> np.ndarray:
    if XGBRegressor is None:
        return forecast_additive_recursive(
            train_t,
            train_dates,
            steps,
            lag_steps=lag_steps,
            policy_map=policy_map,
            noise_level=noise_level,
            rng=rng,
        )

    min_required = _required_history(lag_steps)
    if len(train_t) <= min_required + 4:
        return _mean_fallback(train_t, steps)

    X_train, y_train = build_supervised_matrix(
        train_t,
        series_dates=train_dates,
        lag_steps=lag_steps,
        policy_map=policy_map,
        noise_level=noise_level,
        rng=rng,
    )
    if len(X_train) == 0:
        return _mean_fallback(train_t, steps)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=seed,
        n_jobs=1,
        verbosity=0,
    )
    model.fit(X_scaled, y_train)

    history = np.asarray(train_t, dtype=float).tolist()
    last_train_date = pd.Timestamp(train_dates.iloc[-1])
    preds = []
    for step_idx in range(1, steps + 1):
        target_date = last_train_date + pd.DateOffset(months=step_idx)
        x_next = _make_feature_row(
            history,
            target_date=target_date,
            lag_steps=lag_steps,
            policy_map=policy_map,
        ).reshape(1, -1)
        if noise_level > 0:
            local_rng = rng if rng is not None else np.random.default_rng(seed)
            x_next = _inject_exogenous_noise(x_next.flatten(), noise_level=noise_level, rng=local_rng).reshape(1, -1)
        x_next_scaled = scaler.transform(x_next)
        pred = float(model.predict(x_next_scaled)[0])
        preds.append(pred)
        history.append(pred)

    return np.asarray(preds, dtype=float)


def _fit_stat_model(train_t: np.ndarray, seasonal_period: int):
    use_sarima = len(train_t) >= (seasonal_period + 8)
    if use_sarima:
        try:
            return ARIMA(train_t, order=(1, 1, 1), seasonal_order=(1, 1, 1, seasonal_period)).fit(), "SARIMA"
        except Exception:
            pass
    try:
        return ARIMA(train_t, order=(1, 1, 1)).fit(), "ARIMA"
    except Exception:
        return ARIMA(train_t, order=(1, 1, 0)).fit(), "ARIMA"


def _bootstrap_prediction_intervals(
    point_forecast_t: np.ndarray,
    residual_errors_t: np.ndarray,
    alpha: float,
    n_samples: int,
) -> Tuple[np.ndarray, np.ndarray]:
    if len(residual_errors_t) == 0:
        return point_forecast_t.copy(), point_forecast_t.copy()

    errors = np.asarray(residual_errors_t, dtype=float)
    point = np.asarray(point_forecast_t, dtype=float)
    steps = len(point)

    sampled = np.random.choice(errors, size=(n_samples, steps), replace=True)
    sampled_forecasts = point.reshape(1, -1) + sampled

    lower = np.quantile(sampled_forecasts, alpha / 2.0, axis=0)
    upper = np.quantile(sampled_forecasts, 1.0 - alpha / 2.0, axis=0)
    return lower.astype(float), upper.astype(float)


def forecast_hybrid_recursive(
    train_t: np.ndarray,
    train_dates: pd.Series,
    steps: int,
    lag_steps: Tuple[int, ...],
    seasonal_period: int,
    policy_map: Dict[pd.Period, float],
    seed: int,
    alpha: float,
    n_bootstrap_samples: int,
    noise_level: float = 0.0,
    rng: np.random.Generator = None,
) -> Dict[str, np.ndarray]:
    set_seed(seed)

    min_required = _required_history(lag_steps)
    if len(train_t) <= min_required + 8:
        point_pred = _mean_fallback(train_t, steps)
        return {
            "point": point_pred,
            "lower": point_pred.copy(),
            "upper": point_pred.copy(),
        }

    stat_fit, stat_model_name = _fit_stat_model(train_t=train_t, seasonal_period=seasonal_period)
    logging.debug("Hybrid base statistical model selected: %s", stat_model_name)

    arima_forecast = np.asarray(stat_fit.forecast(steps=steps), dtype=float)

    train_n = len(train_t)
    fitted_in_sample = np.asarray(stat_fit.predict(start=1, end=train_n - 1), dtype=float)
    actual_in_sample = np.asarray(train_t[1:], dtype=float)
    residual_series = actual_in_sample - fitted_in_sample

    if len(residual_series) <= min_required + 2:
        final_point = arima_forecast
        lower_t, upper_t = _bootstrap_prediction_intervals(
            point_forecast_t=final_point,
            residual_errors_t=residual_series,
            alpha=alpha,
            n_samples=n_bootstrap_samples,
        )
        return {
            "point": final_point,
            "lower": lower_t,
            "upper": upper_t,
        }

    residual_dates = pd.Series(pd.to_datetime(train_dates.iloc[1:]).values)

    X_res, y_res = build_supervised_matrix(
        residual_series,
        series_dates=residual_dates,
        lag_steps=lag_steps,
        policy_map=policy_map,
        noise_level=noise_level,
        rng=rng,
    )

    if len(X_res) == 0:
        final_point = arima_forecast
        lower_t, upper_t = _bootstrap_prediction_intervals(
            point_forecast_t=final_point,
            residual_errors_t=residual_series,
            alpha=alpha,
            n_samples=n_bootstrap_samples,
        )
        return {
            "point": final_point,
            "lower": lower_t,
            "upper": upper_t,
        }

    scaler = StandardScaler()
    X_res_scaled = scaler.fit_transform(X_res)

    if XGBRegressor is None:
        residual_model = LinearRegression()
    else:
        residual_model = XGBRegressor(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=seed,
            n_jobs=1,
            verbosity=0,
        )
    residual_model.fit(X_res_scaled, y_res)

    residual_history = residual_series.tolist()
    last_residual_date = pd.Timestamp(residual_dates.iloc[-1])
    residual_preds = []
    for step_idx in range(1, steps + 1):
        target_date = last_residual_date + pd.DateOffset(months=step_idx)
        x_next = _make_feature_row(
            residual_history,
            target_date=target_date,
            lag_steps=lag_steps,
            policy_map=policy_map,
        ).reshape(1, -1)
        if noise_level > 0:
            local_rng = rng if rng is not None else np.random.default_rng(seed)
            x_next = _inject_exogenous_noise(x_next.flatten(), noise_level=noise_level, rng=local_rng).reshape(1, -1)
        x_next_scaled = scaler.transform(x_next)
        residual_step_pred = float(residual_model.predict(x_next_scaled)[0])
        residual_preds.append(residual_step_pred)
        residual_history.append(residual_step_pred)

    residual_preds_arr = np.asarray(residual_preds, dtype=float)
    final_point = arima_forecast + residual_preds_arr

    fitted_residual_hat = np.asarray(residual_model.predict(X_res_scaled), dtype=float)
    hybrid_training_errors = y_res - fitted_residual_hat
    lower_t, upper_t = _bootstrap_prediction_intervals(
        point_forecast_t=final_point,
        residual_errors_t=hybrid_training_errors,
        alpha=alpha,
        n_samples=n_bootstrap_samples,
    )

    return {
        "point": final_point,
        "lower": lower_t,
        "upper": upper_t,
    }


def diebold_mariano_test(
    y_true: np.ndarray,
    yhat_a: np.ndarray,
    yhat_b: np.ndarray,
    horizon: int,
) -> Tuple[float, float]:
    y_true = np.asarray(y_true, dtype=float)
    yhat_a = np.asarray(yhat_a, dtype=float)
    yhat_b = np.asarray(yhat_b, dtype=float)

    n = len(y_true)
    if n < max(10, horizon + 2):
        return float("nan"), float("nan")

    d = (y_true - yhat_a) ** 2 - (y_true - yhat_b) ** 2
    d_bar = float(np.mean(d))

    max_lag = max(0, horizon - 1)
    centered = d - d_bar
    gamma0 = float(np.dot(centered, centered) / n)
    long_var = gamma0

    for lag in range(1, max_lag + 1):
        cov = float(np.dot(centered[lag:], centered[:-lag]) / n)
        weight = 1.0 - lag / (max_lag + 1)
        long_var += 2.0 * weight * cov

    if long_var <= 0 or np.isnan(long_var):
        return float("nan"), float("nan")

    dm_stat = d_bar / np.sqrt(long_var / n)
    p_value = 2.0 * (1.0 - norm.cdf(abs(dm_stat)))
    return float(dm_stat), float(p_value)


def build_dm_results(
    predictions_df: pd.DataFrame,
    alpha: float,
    model_a: str = "Hybrid",
    model_b_list: Tuple[str, ...] = ("ARIMA", "Additive", "XGBoost"),
) -> pd.DataFrame:
    rows = []

    for horizon in sorted(predictions_df["horizon"].unique().tolist()):
        ref = predictions_df[
            (predictions_df["model"] == model_a) & (predictions_df["horizon"] == horizon)
        ][["fold", "origin_idx", "forecast_date", "y_true", "y_pred"]].copy()
        ref = ref.rename(columns={"y_pred": "y_pred_a", "y_true": "y_true_a"})

        for model_b in model_b_list:
            cmp_df = predictions_df[
                (predictions_df["model"] == model_b) & (predictions_df["horizon"] == horizon)
            ][["fold", "origin_idx", "forecast_date", "y_true", "y_pred"]].copy()
            cmp_df = cmp_df.rename(columns={"y_pred": "y_pred_b", "y_true": "y_true_b"})

            merged = ref.merge(cmp_df, on=["fold", "origin_idx", "forecast_date"], how="inner")

            if len(merged) == 0:
                dm_stat, p_value = float("nan"), float("nan")
            else:
                dm_stat, p_value = diebold_mariano_test(
                    y_true=merged["y_true_a"].values,
                    yhat_a=merged["y_pred_a"].values,
                    yhat_b=merged["y_pred_b"].values,
                    horizon=int(horizon),
                )

            rows.append(
                {
                    "horizon": int(horizon),
                    "Model A": model_a,
                    "Model B": model_b,
                    "DM statistic": float(dm_stat),
                    "p-value": float(p_value),
                    "Statistically significant (True/False)": bool(p_value < alpha) if not np.isnan(p_value) else False,
                }
            )

    return pd.DataFrame(rows).sort_values(["horizon", "Model B"]).reset_index(drop=True)


def summarize_metrics(predictions_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = predictions_df.groupby(["model", "horizon"], as_index=False)
    for (model, horizon), grp in grouped:
        y_true = grp["y_true"].values.astype(float)
        y_pred = grp["y_pred"].values.astype(float)
        rows.append(
            {
                "model": model,
                "horizon": int(horizon),
                "MAE": mae(y_true, y_pred),
                "RMSE": rmse(y_true, y_pred),
                "MAPE": mape(y_true, y_pred),
                "N": int(len(grp)),
            }
        )
    return pd.DataFrame(rows).sort_values(["horizon", "model"]).reset_index(drop=True)


def summarize_fold_validation(predictions_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = predictions_df.groupby(["fold", "model", "horizon"], as_index=False)
    for (fold, model, horizon), grp in grouped:
        y_true = grp["y_true"].values.astype(float)
        y_pred = grp["y_pred"].values.astype(float)
        rows.append(
            {
                "fold": int(fold),
                "model": model,
                "horizon": int(horizon),
                "MAE": mae(y_true, y_pred),
                "RMSE": rmse(y_true, y_pred),
                "MAPE": mape(y_true, y_pred),
                "N": int(len(grp)),
            }
        )
    return pd.DataFrame(rows).sort_values(["fold", "horizon", "model"]).reset_index(drop=True)


def _evaluate_predictions_under_noise(
    cfg: Config,
    y: np.ndarray,
    y_t: np.ndarray,
    ds: pd.Series,
    policy_map: Dict[pd.Period, float],
    noise_level: float,
) -> pd.DataFrame:
    max_h = max(cfg.horizons)
    initial_train = max(cfg.min_train_points, int(len(y_t) * cfg.initial_train_ratio))
    origins = list(range(initial_train, len(y_t) - max_h + 1, cfg.origin_step))

    rng = np.random.default_rng(cfg.random_seed + int(noise_level * 1000))
    predictions_rows = []

    noisy_models = {
        "Additive": lambda train_t, train_dates: forecast_additive_recursive(
            train_t=train_t,
            train_dates=train_dates,
            steps=max_h,
            lag_steps=cfg.lag_steps,
            policy_map=policy_map,
            noise_level=noise_level,
            rng=rng,
        ),
        "XGBoost": lambda train_t, train_dates: forecast_xgboost_recursive(
            train_t=train_t,
            train_dates=train_dates,
            steps=max_h,
            lag_steps=cfg.lag_steps,
            policy_map=policy_map,
            seed=cfg.random_seed,
            noise_level=noise_level,
            rng=rng,
        ),
        "Hybrid": lambda train_t, train_dates: forecast_hybrid_recursive(
            train_t=train_t,
            train_dates=train_dates,
            steps=max_h,
            lag_steps=cfg.lag_steps,
            seasonal_period=cfg.seasonal_period,
            policy_map=policy_map,
            seed=cfg.random_seed,
            alpha=cfg.interval_alpha,
            n_bootstrap_samples=cfg.n_bootstrap_samples,
            noise_level=noise_level,
            rng=rng,
        ),
    }

    for fold_idx, origin in enumerate(origins, start=1):
        train_t = y_t[:origin]
        train_dates = ds.iloc[:origin].reset_index(drop=True)
        future_true = y[origin:origin + max_h]
        future_dates = ds.iloc[origin:origin + max_h].reset_index(drop=True)

        for model_name, model_fn in noisy_models.items():
            model_output = model_fn(train_t, train_dates)
            if isinstance(model_output, dict):
                pred_t = model_output["point"]
            else:
                pred_t = model_output

            pred = target_inverse_transform(pred_t, use_log1p=cfg.use_log1p)
            for h in cfg.horizons:
                idx = h - 1
                predictions_rows.append(
                    {
                        "fold": fold_idx,
                        "origin_idx": origin,
                        "model": model_name,
                        "horizon": int(h),
                        "forecast_date": str(pd.to_datetime(future_dates.iloc[idx]).date()),
                        "y_true": float(future_true[idx]),
                        "y_pred": float(pred[idx]),
                    }
                )

    return pd.DataFrame(predictions_rows)


def _export_table_variants(df: pd.DataFrame, output_dir: str, base_name: str) -> None:
    csv_path = os.path.join(output_dir, f"{base_name}.csv")
    md_path = os.path.join(output_dir, f"{base_name}.md")
    tex_path = os.path.join(output_dir, f"{base_name}.tex")

    df.to_csv(csv_path, index=False)

    try:
        md_text = df.to_markdown(index=False)
    except Exception:
        header = "| " + " | ".join(df.columns.tolist()) + " |"
        sep = "| " + " | ".join(["---"] * len(df.columns)) + " |"
        rows = []
        for _, row in df.iterrows():
            vals = [str(row[col]) for col in df.columns]
            rows.append("| " + " | ".join(vals) + " |")
        md_text = "\n".join([header, sep] + rows)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
        f.write("\n")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(df.to_latex(index=False, float_format="%.4f"))


def run_robustness_testing(
    cfg: Config,
    baseline_metrics_df: pd.DataFrame,
    y: np.ndarray,
    y_t: np.ndarray,
    ds: pd.Series,
    policy_map: Dict[pd.Period, float],
    noise_levels: Tuple[float, ...] = (0.05, 0.10, 0.20),
) -> Dict[str, pd.DataFrame]:
    baseline_subset = baseline_metrics_df[baseline_metrics_df["model"].isin(["Additive", "XGBoost", "Hybrid"])][
        ["model", "horizon", "MAE", "RMSE"]
    ].rename(columns={"MAE": "MAE_baseline", "RMSE": "RMSE_baseline"})

    degradation_rows = []
    for noise in noise_levels:
        noisy_predictions = _evaluate_predictions_under_noise(
            cfg=cfg,
            y=y,
            y_t=y_t,
            ds=ds,
            policy_map=policy_map,
            noise_level=noise,
        )
        noisy_metrics = summarize_metrics(noisy_predictions)[["model", "horizon", "MAE", "RMSE"]]
        noisy_metrics = noisy_metrics.rename(columns={"MAE": "MAE_noisy", "RMSE": "RMSE_noisy"})

        merged = noisy_metrics.merge(baseline_subset, on=["model", "horizon"], how="inner")
        merged["noise_level"] = float(noise)
        merged["noise_level_pct"] = float(noise * 100.0)
        merged["MAE_degradation"] = merged["MAE_noisy"] - merged["MAE_baseline"]
        merged["RMSE_degradation"] = merged["RMSE_noisy"] - merged["RMSE_baseline"]
        merged["MAE_degradation_pct"] = np.where(
            merged["MAE_baseline"] == 0,
            0.0,
            100.0 * merged["MAE_degradation"] / merged["MAE_baseline"],
        )
        merged["RMSE_degradation_pct"] = np.where(
            merged["RMSE_baseline"] == 0,
            0.0,
            100.0 * merged["RMSE_degradation"] / merged["RMSE_baseline"],
        )

        degradation_rows.append(merged)

    degradation_df = pd.concat(degradation_rows, ignore_index=True)
    degradation_df = degradation_df.sort_values(["model", "horizon", "noise_level"]).reset_index(drop=True)

    summary_df = (
        degradation_df.groupby(["model", "noise_level", "noise_level_pct"], as_index=False)
        .agg(
            MAE_baseline=("MAE_baseline", "mean"),
            MAE_noisy=("MAE_noisy", "mean"),
            MAE_degradation=("MAE_degradation", "mean"),
            MAE_degradation_pct=("MAE_degradation_pct", "mean"),
            RMSE_baseline=("RMSE_baseline", "mean"),
            RMSE_noisy=("RMSE_noisy", "mean"),
            RMSE_degradation=("RMSE_degradation", "mean"),
            RMSE_degradation_pct=("RMSE_degradation_pct", "mean"),
        )
        .sort_values(["model", "noise_level"])
        .reset_index(drop=True)
    )

    _export_table_variants(degradation_df, cfg.output_dir, "robustness_degradation_detailed")
    _export_table_variants(summary_df, cfg.output_dir, "robustness_degradation_summary")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharex=True)
    for model_name in sorted(summary_df["model"].unique().tolist()):
        model_df = summary_df[summary_df["model"] == model_name].sort_values("noise_level_pct")
        axes[0].plot(model_df["noise_level_pct"], model_df["MAE_noisy"], marker="o", linewidth=2, label=model_name)
        axes[1].plot(model_df["noise_level_pct"], model_df["RMSE_noisy"], marker="o", linewidth=2, label=model_name)

    axes[0].set_title("MAE vs Noise Level")
    axes[0].set_xlabel("Noise Level (%)")
    axes[0].set_ylabel("MAE")
    axes[0].grid(True, alpha=0.3)

    axes[1].set_title("RMSE vs Noise Level")
    axes[1].set_xlabel("Noise Level (%)")
    axes[1].set_ylabel("RMSE")
    axes[1].grid(True, alpha=0.3)

    axes[1].legend(loc="best")
    fig.suptitle("Robustness Test: Forecast Error vs Exogenous Noise", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])

    plot_png = os.path.join(cfg.output_dir, "robustness_error_vs_noise.png")
    plot_pdf = os.path.join(cfg.output_dir, "robustness_error_vs_noise.pdf")
    fig.savefig(plot_png, dpi=300, bbox_inches="tight")
    fig.savefig(plot_pdf, dpi=300, bbox_inches="tight")
    plt.close(fig)

    plots_df = pd.DataFrame(
        [
            {
                "figure": "robustness_error_vs_noise",
                "png_path": plot_png,
                "pdf_path": plot_pdf,
            }
        ]
    )
    plots_df.to_csv(os.path.join(cfg.output_dir, "robustness_plots_manifest.csv"), index=False)

    return {
        "robustness_detailed": degradation_df,
        "robustness_summary": summary_df,
        "robustness_plots": plots_df,
    }


def run_backtest(cfg: Config) -> Dict[str, pd.DataFrame]:
    output_dir = prepare_experiment_output_dir(cfg)
    log_path = setup_experiment_logger(output_dir=output_dir, experiment_name=cfg.experiment_name)
    set_seed(cfg.random_seed)
    save_experiment_manifest(cfg=cfg, output_dir=output_dir, log_path=log_path)

    logging.info("Starting forecasting experiment | name=%s | run_id=%s", cfg.experiment_name, cfg.run_id)
    logging.info("Resolved config: %s", json.dumps(_config_to_serializable_dict(cfg), sort_keys=True))
    logging.info("Model hyperparameters: %s", json.dumps(build_model_hyperparameters(cfg), sort_keys=True))

    series_df = load_series(cfg)
    y = series_df["y"].values.astype(float)
    ds = pd.to_datetime(series_df["ds"])
    policy_map = _build_policy_map(cfg.policy_events)
    y_t = target_transform(y, use_log1p=cfg.use_log1p)

    max_h = max(cfg.horizons)
    initial_train = max(cfg.min_train_points, int(len(y_t) * cfg.initial_train_ratio))
    if initial_train + max_h > len(y_t):
        raise ValueError(
            f"Insufficient data for rolling-origin CV: n={len(y_t)}, initial_train={initial_train}, max_h={max_h}"
        )

    origins = list(range(initial_train, len(y_t) - max_h + 1, cfg.origin_step))
    if len(origins) == 0:
        raise ValueError("No valid rolling-origin splits were generated. Adjust initial_train_ratio/origin_step.")

    model_functions = {
        "ARIMA": lambda train_t, train_dates: forecast_arima(train_t=train_t, steps=max_h),
        "SARIMA": lambda train_t, train_dates: forecast_sarima(
            train_t=train_t,
            steps=max_h,
            seasonal_period=cfg.seasonal_period,
        ),
        "Additive": lambda train_t, train_dates: forecast_additive_recursive(
            train_t=train_t,
            train_dates=train_dates,
            steps=max_h,
            lag_steps=cfg.lag_steps,
            policy_map=policy_map,
        ),
        "XGBoost": lambda train_t, train_dates: forecast_xgboost_recursive(
            train_t=train_t,
            train_dates=train_dates,
            steps=max_h,
            lag_steps=cfg.lag_steps,
            policy_map=policy_map,
            seed=cfg.random_seed,
        ),
        "Hybrid": lambda train_t, train_dates: forecast_hybrid_recursive(
            train_t=train_t,
            train_dates=train_dates,
            steps=max_h,
            lag_steps=cfg.lag_steps,
            seasonal_period=cfg.seasonal_period,
            policy_map=policy_map,
            seed=cfg.random_seed,
            alpha=cfg.interval_alpha,
            n_bootstrap_samples=cfg.n_bootstrap_samples,
        ),
    }

    predictions_rows = []
    windows_rows = []
    runtime_rows = []

    for fold_idx, origin in enumerate(origins, start=1):
        train_t = y_t[:origin]
        train_dates = ds.iloc[:origin].reset_index(drop=True)
        future_true = y[origin:origin + max_h]
        future_dates = ds.iloc[origin:origin + max_h].reset_index(drop=True)

        train_start = str(pd.to_datetime(ds.iloc[0]).date())
        train_end = str(pd.to_datetime(ds.iloc[origin - 1]).date())
        test_start = str(pd.to_datetime(future_dates.iloc[0]).date())
        test_end = str(pd.to_datetime(future_dates.iloc[-1]).date())

        logging.info(
            "Fold %s | train=[%s to %s] (%s points) | test=[%s to %s] (%s points)",
            fold_idx,
            train_start,
            train_end,
            len(train_t),
            test_start,
            test_end,
            len(future_true),
        )

        windows_rows.append(
            {
                "fold": fold_idx,
                "origin_idx": origin,
                "train_start": train_start,
                "train_end": train_end,
                "train_points": int(len(train_t)),
                "test_start": test_start,
                "test_end": test_end,
                "test_points": int(len(future_true)),
            }
        )

        for model_name, model_fn in model_functions.items():
            t0 = time.time()
            model_output = model_fn(train_t, train_dates)
            if isinstance(model_output, dict):
                pred_t = model_output["point"]
                pred_t_lower = model_output.get("lower", pred_t)
                pred_t_upper = model_output.get("upper", pred_t)
            else:
                pred_t = model_output
                pred_t_lower = model_output
                pred_t_upper = model_output

            pred = target_inverse_transform(pred_t, use_log1p=cfg.use_log1p)
            pred_lower = target_inverse_transform(pred_t_lower, use_log1p=cfg.use_log1p)
            pred_upper = target_inverse_transform(pred_t_upper, use_log1p=cfg.use_log1p)
            runtime_rows.append(
                {
                    "experiment_name": cfg.experiment_name,
                    "run_id": cfg.run_id,
                    "fold": fold_idx,
                    "model": model_name,
                    "seed": int(cfg.random_seed),
                    "train_start": train_start,
                    "train_end": train_end,
                    "test_start": test_start,
                    "test_end": test_end,
                    "runtime_sec": round(time.time() - t0, 4),
                }
            )

            for h in cfg.horizons:
                idx = h - 1
                predictions_rows.append(
                    {
                        "fold": fold_idx,
                        "origin_idx": origin,
                        "model": model_name,
                        "experiment_name": cfg.experiment_name,
                        "run_id": cfg.run_id,
                        "horizon": int(h),
                        "forecast_date": str(pd.to_datetime(future_dates[idx]).date()),
                        "y_true": float(future_true[idx]),
                        "y_pred": float(pred[idx]),
                        "y_pred_lower": float(pred_lower[idx]) if model_name == "Hybrid" else float("nan"),
                        "y_pred_upper": float(pred_upper[idx]) if model_name == "Hybrid" else float("nan"),
                        "train_start": train_start,
                        "train_end": train_end,
                        "test_start": test_start,
                        "test_end": test_end,
                    }
                )

    predictions_df = pd.DataFrame(predictions_rows)
    metrics_df = summarize_metrics(predictions_df)
    fold_validation_df = summarize_fold_validation(predictions_df)
    dm_results_df = build_dm_results(predictions_df=predictions_df, alpha=cfg.dm_alpha)
    windows_df = pd.DataFrame(windows_rows)
    runtime_df = pd.DataFrame(runtime_rows)

    metrics_df.insert(0, "experiment_name", cfg.experiment_name)
    metrics_df.insert(1, "run_id", cfg.run_id)
    fold_validation_df.insert(0, "experiment_name", cfg.experiment_name)
    fold_validation_df.insert(1, "run_id", cfg.run_id)
    dm_results_df.insert(0, "experiment_name", cfg.experiment_name)
    dm_results_df.insert(1, "run_id", cfg.run_id)
    windows_df.insert(0, "experiment_name", cfg.experiment_name)
    windows_df.insert(1, "run_id", cfg.run_id)

    predictions_df.to_csv(os.path.join(cfg.output_dir, "predictions_all.csv"), index=False)
    metrics_df.to_csv(os.path.join(cfg.output_dir, "metrics_by_seed_model_horizon.csv"), index=False)
    fold_validation_df.to_csv(os.path.join(cfg.output_dir, "validation_fold_results.csv"), index=False)
    dm_results_df.to_csv(os.path.join(cfg.output_dir, "dm_test_results.csv"), index=False)
    windows_df.to_csv(os.path.join(cfg.output_dir, "rolling_windows_log.csv"), index=False)
    runtime_df.to_csv(os.path.join(cfg.output_dir, "runtime_log.csv"), index=False)
    runtime_df.to_csv(os.path.join(cfg.output_dir, "training_log.csv"), index=False)
    metrics_df.to_csv(os.path.join(cfg.output_dir, "validation_summary.csv"), index=False)

    figures_df = generate_forecast_visualizations(
        predictions_df=predictions_df,
        output_dir=cfg.output_dir,
        horizons=cfg.horizons,
    )
    figures_df.to_csv(os.path.join(cfg.output_dir, "forecast_figures_manifest.csv"), index=False)

    robustness_outputs = run_robustness_testing(
        cfg=cfg,
        baseline_metrics_df=metrics_df,
        y=y,
        y_t=y_t,
        ds=ds,
        policy_map=policy_map,
    )

    hardware_meta = {
        "experiment_name": cfg.experiment_name,
        "run_id": cfg.run_id,
        "config_path": cfg.config_path,
        "output_dir": cfg.output_dir,
        "log_path": log_path,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "dataset_points": int(len(series_df)),
        "num_folds": int(len(origins)),
        "horizons": [int(h) for h in cfg.horizons],
        "models": list(model_functions.keys()),
        "use_log1p": bool(cfg.use_log1p),
        "max_lag": int(cfg.max_lag),
        "lag_steps": [int(lg) for lg in cfg.lag_steps],
        "seasonal_period": int(cfg.seasonal_period),
        "rolling_windows": [int(w) for w in cfg.rolling_windows],
        "feature_columns": list(FEATURE_COLUMNS),
        "policy_events": [{"date": d, "intensity": float(s)} for d, s in cfg.policy_events],
        "interval_alpha": float(cfg.interval_alpha),
        "n_bootstrap_samples": int(cfg.n_bootstrap_samples),
        "dm_alpha": float(cfg.dm_alpha),
        "robustness_noise_levels": [5, 10, 20],
        "robustness_exogenous_features": list(EXOGENOUS_FEATURE_COLUMNS),
        "model_hyperparameters": build_model_hyperparameters(cfg),
    }
    with open(os.path.join(cfg.output_dir, "hardware_and_config.json"), "w", encoding="utf-8") as f:
        json.dump(hardware_meta, f, indent=2)

    best_by_horizon = (
        metrics_df.sort_values(["horizon", "RMSE", "MAE", "MAPE"])
        .groupby("horizon", as_index=False)
        .first()[["horizon", "model", "RMSE", "MAE", "MAPE"]]
        .rename(columns={"model": "best_model"})
    )
    experiment_summary = {
        "experiment_name": cfg.experiment_name,
        "run_id": cfg.run_id,
        "config_path": cfg.config_path,
        "random_seed": int(cfg.random_seed),
        "dataset_points": int(len(series_df)),
        "num_folds": int(len(origins)),
        "models": list(model_functions.keys()),
        "best_models_by_horizon": best_by_horizon.to_dict(orient="records"),
        "artifacts": {
            "predictions": "predictions_all.csv",
            "metrics": "metrics_by_seed_model_horizon.csv",
            "validation_folds": "validation_fold_results.csv",
            "training_log": "training_log.csv",
            "validation_summary": "validation_summary.csv",
            "runtime_log": "runtime_log.csv",
            "dm_results": "dm_test_results.csv",
            "rolling_windows": "rolling_windows_log.csv",
            "figures_manifest": "forecast_figures_manifest.csv",
            "manifest": "experiment_manifest.json",
        },
    }
    with open(os.path.join(cfg.output_dir, "experiment_summary.json"), "w", encoding="utf-8") as f:
        json.dump(experiment_summary, f, indent=2)

    logging.info("Validation summary saved: %s", os.path.join(cfg.output_dir, "validation_summary.csv"))
    logging.info("Training log saved: %s", os.path.join(cfg.output_dir, "training_log.csv"))
    logging.info("Experiment manifest saved: %s", os.path.join(cfg.output_dir, "experiment_manifest.json"))

    logging.info("Backtest completed | folds=%s | outputs=%s", len(origins), cfg.output_dir)

    return {
        "metrics": metrics_df,
        "fold_validation": fold_validation_df,
        "dm_results": dm_results_df,
        "predictions": predictions_df,
        "windows": windows_df,
        "runtime": runtime_df,
        "figures": figures_df,
        **robustness_outputs,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Reproducible forecasting backtest runner")
    parser.add_argument("--config", type=str, default="", help="Path to JSON/YAML experiment config file")
    parser.add_argument("--experiment-name", type=str, default="", help="Override experiment name")
    parser.add_argument("--run-id", type=str, default="", help="Optional fixed run identifier for reruns")
    parser.add_argument("--output-dir", type=str, default="", help="Optional explicit output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = load_experiment_config(args.config) if args.config else Config()
    if args.experiment_name:
        cfg.experiment_name = args.experiment_name
    if args.run_id:
        cfg.run_id = args.run_id
    if args.output_dir:
        cfg.output_dir = args.output_dir
    outputs = run_backtest(cfg)
    print("\nMetrics summary:")
    print(outputs["metrics"].to_string(index=False))
    print("\nDiebold-Mariano test results:")
    print(outputs["dm_results"].to_string(index=False))
    print("\nGenerated figures:")
    print(outputs["figures"].to_string(index=False))
    print("\nRobustness degradation summary:")
    print(outputs["robustness_summary"].to_string(index=False))
