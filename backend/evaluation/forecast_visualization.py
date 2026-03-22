import os
from typing import Iterable, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _configure_publication_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.titleweight": "bold",
            "axes.labelweight": "bold",
        }
    )


def _ensure_datetime(predictions_df: pd.DataFrame) -> pd.DataFrame:
    plot_df = predictions_df.copy()
    plot_df["forecast_date"] = pd.to_datetime(plot_df["forecast_date"], errors="coerce")
    plot_df = plot_df.dropna(subset=["forecast_date"]).sort_values("forecast_date")
    return plot_df


def _save_publication_figure(fig: plt.Figure, output_base_path: str) -> Tuple[str, str]:
    png_path = f"{output_base_path}.png"
    pdf_path = f"{output_base_path}.pdf"
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    return png_path, pdf_path


def plot_actual_vs_predicted_horizons(
    predictions_df: pd.DataFrame,
    output_dir: str,
    horizons: Iterable[int] = (1, 3, 6, 12),
    models: Iterable[str] = ("ARIMA", "SARIMA", "Additive", "XGBoost", "Hybrid"),
) -> Tuple[str, str]:
    _configure_publication_style()
    os.makedirs(output_dir, exist_ok=True)

    plot_df = _ensure_datetime(predictions_df)
    horizons = list(horizons)
    models = list(models)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=False, sharey=False)
    axes = axes.flatten()

    model_colors = {
        "ARIMA": "#1f77b4",
        "SARIMA": "#2ca02c",
        "Additive": "#ff7f0e",
        "XGBoost": "#9467bd",
        "Hybrid": "#d62728",
    }

    for ax, horizon in zip(axes, horizons):
        horizon_df = plot_df[plot_df["horizon"] == horizon].copy()
        if horizon_df.empty:
            ax.set_title(f"Horizon {horizon} Months (No Data)")
            continue

        actual_df = (
            horizon_df[["forecast_date", "y_true"]]
            .drop_duplicates(subset=["forecast_date"])
            .sort_values("forecast_date")
        )
        ax.plot(
            actual_df["forecast_date"],
            actual_df["y_true"],
            color="black",
            linewidth=2.2,
            label="Actual",
        )

        for model_name in models:
            model_df = horizon_df[horizon_df["model"] == model_name].sort_values("forecast_date")
            if model_df.empty:
                continue

            color = model_colors.get(model_name, None)
            ax.plot(
                model_df["forecast_date"],
                model_df["y_pred"],
                linewidth=1.8,
                label=f"{model_name} Predicted",
                color=color,
                marker="o",
                markersize=3,
                alpha=0.9,
            )

            has_ci = (
                model_df.get("y_pred_lower") is not None
                and model_df["y_pred_lower"].notna().any()
                and model_df.get("y_pred_upper") is not None
                and model_df["y_pred_upper"].notna().any()
            )
            if has_ci:
                lower = model_df["y_pred_lower"].values.astype(float)
                upper = model_df["y_pred_upper"].values.astype(float)
                ax.fill_between(
                    model_df["forecast_date"],
                    lower,
                    upper,
                    color=color if color else "gray",
                    alpha=0.15,
                    label=f"{model_name} 95% CI",
                )

        forecast_start = actual_df["forecast_date"].min()
        ax.axvline(
            forecast_start,
            color="gray",
            linestyle="--",
            linewidth=1.2,
            alpha=0.9,
            label="Forecast Horizon Marker",
        )

        ax.set_title(f"Actual vs Predicted ({horizon}-Month Horizon)")
        ax.set_xlabel("Forecast Date")
        ax.set_ylabel("Sales Quantity")
        ax.legend(loc="best", frameon=True)

    fig.suptitle("Automotive Forecasting: Actual vs Predicted Across Horizons", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.01, 1, 0.97])

    return _save_publication_figure(fig, os.path.join(output_dir, "forecast_actual_vs_predicted_horizons"))


def plot_hybrid_forecast_intervals(
    predictions_df: pd.DataFrame,
    output_dir: str,
    horizons: Iterable[int] = (1, 3, 6, 12),
) -> Tuple[str, str]:
    _configure_publication_style()
    os.makedirs(output_dir, exist_ok=True)

    plot_df = _ensure_datetime(predictions_df)
    hybrid_df = plot_df[plot_df["model"] == "Hybrid"].copy()

    fig, ax = plt.subplots(figsize=(14, 7))

    actual_df = (
        hybrid_df[["forecast_date", "y_true"]]
        .drop_duplicates(subset=["forecast_date"])
        .sort_values("forecast_date")
    )
    ax.plot(
        actual_df["forecast_date"],
        actual_df["y_true"],
        color="black",
        linewidth=2.4,
        label="Actual",
    )

    horizon_markers = {1: "o", 3: "s", 6: "^", 12: "D"}
    horizon_colors = {1: "#1f77b4", 3: "#ff7f0e", 6: "#2ca02c", 12: "#d62728"}

    for horizon in horizons:
        h_df = hybrid_df[hybrid_df["horizon"] == horizon].sort_values("forecast_date")
        if h_df.empty:
            continue

        color = horizon_colors.get(horizon, "#9467bd")
        marker = horizon_markers.get(horizon, "o")
        ax.plot(
            h_df["forecast_date"],
            h_df["y_pred"],
            linestyle="-",
            linewidth=1.8,
            marker=marker,
            markersize=4,
            color=color,
            label=f"Hybrid {horizon}-Month Forecast",
        )

        if h_df["y_pred_lower"].notna().any() and h_df["y_pred_upper"].notna().any():
            ax.fill_between(
                h_df["forecast_date"],
                h_df["y_pred_lower"].values.astype(float),
                h_df["y_pred_upper"].values.astype(float),
                color=color,
                alpha=0.12,
                label=f"Hybrid {horizon}-Month 95% CI",
            )

        marker_date = h_df["forecast_date"].min()
        ax.axvline(
            marker_date,
            color=color,
            linestyle="--",
            linewidth=1.0,
            alpha=0.6,
            label=f"{horizon}-Month Horizon Marker",
        )

    ax.set_title("Hybrid Forecast with 95% Confidence Intervals by Horizon")
    ax.set_xlabel("Forecast Date")
    ax.set_ylabel("Sales Quantity")
    ax.legend(loc="best", ncol=2, frameon=True)
    fig.tight_layout()

    return _save_publication_figure(fig, os.path.join(output_dir, "hybrid_forecast_intervals_by_horizon"))


def generate_forecast_visualizations(
    predictions_df: pd.DataFrame,
    output_dir: str,
    horizons: Iterable[int] = (1, 3, 6, 12),
) -> pd.DataFrame:
    outputs = []

    horizon_png, horizon_pdf = plot_actual_vs_predicted_horizons(
        predictions_df=predictions_df,
        output_dir=output_dir,
        horizons=horizons,
    )
    outputs.append({"figure": "actual_vs_predicted_horizons", "png_path": horizon_png, "pdf_path": horizon_pdf})

    hybrid_png, hybrid_pdf = plot_hybrid_forecast_intervals(
        predictions_df=predictions_df,
        output_dir=output_dir,
        horizons=horizons,
    )
    outputs.append({"figure": "hybrid_forecast_intervals", "png_path": hybrid_png, "pdf_path": hybrid_pdf})

    return pd.DataFrame(outputs)
