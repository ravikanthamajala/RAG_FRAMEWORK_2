from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


@dataclass
class PreprocessingConfig:
    date_col: str = "Date"
    target_col: str = "EV_Sales_Quantity"
    monthly_freq: str = "MS"
    monthly_aggregation: str = "sum"
    interpolation_method: str = "linear"
    outlier_method: str = "iqr"
    outlier_action: str = "interpolate"
    zscore_threshold: float = 3.0
    iqr_multiplier: float = 1.5
    non_negative_target: bool = True
    test_ratio: float = 0.2
    min_train_points: int = 24
    scale_feature_columns: Tuple[str, ...] = field(default_factory=tuple)


@dataclass
class PreprocessingArtifacts:
    cleaned_df: pd.DataFrame
    outlier_mask: pd.Series
    summary: Dict[str, float]


class ForecastPreprocessingPipeline:
    """Reusable preprocessing pipeline for automotive forecasting datasets."""

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.scaler: Optional[StandardScaler] = None
        self.scaler_feature_columns: List[str] = []

    def preprocess_target_series(self, df: pd.DataFrame) -> PreprocessingArtifacts:
        monthly_df = self.normalize_to_monthly_frequency(df)
        monthly_df = self.interpolate_missing_values(monthly_df)
        outlier_mask = self.detect_outliers(monthly_df["y"])
        cleaned_df = self.handle_outliers(monthly_df, outlier_mask)
        cleaned_df = self.interpolate_missing_values(cleaned_df)

        if self.config.non_negative_target:
            cleaned_df["y"] = cleaned_df["y"].clip(lower=0.0)

        cleaned_df = cleaned_df.dropna(subset=["ds", "y"]).sort_values("ds").reset_index(drop=True)

        summary = {
            "input_rows": float(len(df)),
            "monthly_rows": float(len(monthly_df)),
            "missing_points_after_monthly_alignment": float(monthly_df["y"].isna().sum()),
            "outliers_detected": float(outlier_mask.sum()),
            "date_start": cleaned_df["ds"].min().value if not cleaned_df.empty else np.nan,
            "date_end": cleaned_df["ds"].max().value if not cleaned_df.empty else np.nan,
        }
        return PreprocessingArtifacts(cleaned_df=cleaned_df, outlier_mask=outlier_mask, summary=summary)

    def normalize_to_monthly_frequency(self, df: pd.DataFrame) -> pd.DataFrame:
        working = df.copy()
        working[self.config.date_col] = pd.to_datetime(working[self.config.date_col], errors="coerce")
        working[self.config.target_col] = pd.to_numeric(working[self.config.target_col], errors="coerce")
        working = working.dropna(subset=[self.config.date_col]).sort_values(self.config.date_col)

        grouped = (
            working.groupby(pd.Grouper(key=self.config.date_col, freq=self.config.monthly_freq))[self.config.target_col]
            .agg(self.config.monthly_aggregation)
            .reset_index()
            .rename(columns={self.config.date_col: "ds", self.config.target_col: "y"})
            .sort_values("ds")
            .reset_index(drop=True)
        )
        if grouped.empty:
            return grouped

        full_index = pd.date_range(grouped["ds"].min(), grouped["ds"].max(), freq=self.config.monthly_freq)
        grouped = (
            grouped.set_index("ds")
            .reindex(full_index)
            .rename_axis("ds")
            .reset_index()
        )
        return grouped

    def interpolate_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        working = df.copy().sort_values("ds").reset_index(drop=True)
        if working.empty:
            return working

        if self.config.interpolation_method == "time":
            indexed = working.set_index("ds")
            indexed["y"] = indexed["y"].interpolate(method="time", limit_direction="both")
            working = indexed.reset_index()
        else:
            working["y"] = working["y"].interpolate(
                method=self.config.interpolation_method,
                limit_direction="both",
            )
        return working

    def detect_outliers(self, series: pd.Series) -> pd.Series:
        y = pd.to_numeric(series, errors="coerce")
        mask = pd.Series(False, index=series.index)
        valid = y.dropna()
        if valid.empty:
            return mask

        if self.config.outlier_method.lower() == "zscore":
            std = float(valid.std(ddof=0))
            if std <= 1e-12:
                return mask
            zscores = (y - float(valid.mean())) / std
            return zscores.abs() > self.config.zscore_threshold

        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        iqr = q3 - q1
        if iqr <= 1e-12:
            return mask
        lower = q1 - self.config.iqr_multiplier * iqr
        upper = q3 + self.config.iqr_multiplier * iqr
        return (y < lower) | (y > upper)

    def handle_outliers(self, df: pd.DataFrame, outlier_mask: pd.Series) -> pd.DataFrame:
        working = df.copy()
        if working.empty:
            return working

        if self.config.outlier_action == "clip":
            valid = working.loc[~outlier_mask, "y"].dropna()
            if valid.empty:
                return working
            if self.config.outlier_method.lower() == "zscore":
                mean = float(valid.mean())
                std = float(valid.std(ddof=0))
                lower = mean - self.config.zscore_threshold * std
                upper = mean + self.config.zscore_threshold * std
            else:
                q1 = float(valid.quantile(0.25))
                q3 = float(valid.quantile(0.75))
                iqr = q3 - q1
                lower = q1 - self.config.iqr_multiplier * iqr
                upper = q3 + self.config.iqr_multiplier * iqr
            working.loc[:, "y"] = working["y"].clip(lower=lower, upper=upper)
            return working

        working.loc[outlier_mask, "y"] = np.nan
        return working

    def fit_feature_scaler(self, train_df: pd.DataFrame, feature_columns: Optional[Sequence[str]] = None) -> StandardScaler:
        feature_columns = list(feature_columns or self.config.scale_feature_columns)
        if not feature_columns:
            raise ValueError("No feature columns supplied for scaling.")
        self.scaler = StandardScaler()
        self.scaler_feature_columns = feature_columns
        self.scaler.fit(train_df[feature_columns])
        return self.scaler

    def transform_feature_frame(self, df: pd.DataFrame, feature_columns: Optional[Sequence[str]] = None) -> pd.DataFrame:
        feature_columns = list(feature_columns or self.scaler_feature_columns or self.config.scale_feature_columns)
        if not feature_columns:
            return df.copy()
        if self.scaler is None:
            raise ValueError("Feature scaler has not been fitted.")

        transformed = df.copy()
        transformed.loc[:, feature_columns] = self.scaler.transform(transformed[feature_columns])
        return transformed

    def scale_train_test_features(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        feature_columns: Optional[Sequence[str]] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
        scaler = self.fit_feature_scaler(train_df, feature_columns=feature_columns)
        return (
            self.transform_feature_frame(train_df, feature_columns=feature_columns),
            self.transform_feature_frame(test_df, feature_columns=feature_columns),
            scaler,
        )

    def time_aware_split(
        self,
        df: pd.DataFrame,
        test_ratio: Optional[float] = None,
        test_size: Optional[int] = None,
        min_train_points: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        working = df.copy().sort_values("ds").reset_index(drop=True)
        if working.empty:
            return working, working.copy()

        ratio = self.config.test_ratio if test_ratio is None else test_ratio
        min_train = self.config.min_train_points if min_train_points is None else min_train_points

        if test_size is None:
            test_size = max(1, int(round(len(working) * ratio)))
        test_size = min(test_size, max(1, len(working) - min_train))
        split_idx = len(working) - test_size

        if split_idx < min_train:
            split_idx = min_train
        if split_idx >= len(working):
            split_idx = len(working) - 1

        train_df = working.iloc[:split_idx].reset_index(drop=True)
        test_df = working.iloc[split_idx:].reset_index(drop=True)
        return train_df, test_df
