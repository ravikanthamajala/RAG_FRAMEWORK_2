"""
Pydantic Schemas for Forecasting API

Validates inputs, outputs, and internal data structures.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import numpy as np


class ForecastRequest(BaseModel):
    """Request schema for forecasting endpoint."""
    
    column_name: str = Field(..., min_length=1, max_length=200)
    periods: int = Field(default=24, ge=3, le=120)
    model_preference: Literal["auto", "arima", "xgboost", "prophet", "ensemble"] = "auto"
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)
    min_data_points: int = Field(default=12, ge=5)
    
    @field_validator('periods')
    @classmethod
    def validate_periods(cls, v):
        if v % 3 != 0:
            raise ValueError("Periods should be divisible by 3 for quarterly alignment")
        return v


class DataQualityMetrics(BaseModel):
    """Data quality assessment."""
    
    total_points: int
    missing_values: int
    missing_percentage: float
    outliers_detected: int
    date_gaps: int
    seasonality_detected: bool
    trend_direction: Literal["increasing", "decreasing", "stable", "volatile"]
    stationarity_test_pvalue: float
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    @model_validator(mode='after')
    def calculate_quality_score(self):
        """Calculate composite quality score if not provided."""
        if self.quality_score is None:
            missing_penalty = self.missing_percentage * 0.3
            outlier_penalty = min(self.outliers_detected / max(self.total_points, 1), 0.2)
            gap_penalty = min(self.date_gaps / max(self.total_points, 1), 0.2)
            
            score = 1.0 - (missing_penalty + outlier_penalty + gap_penalty)
            self.quality_score = max(0.0, min(1.0, score))
        return self


class ModelMetrics(BaseModel):
    """Model performance metrics."""
    
    mae: float = Field(ge=0)
    rmse: float = Field(ge=0)
    mape: Optional[float] = Field(default=None, ge=0, le=1000)
    r2_score: float
    adjusted_r2: Optional[float] = None
    aic: Optional[float] = None
    bic: Optional[float] = None
    
    @field_validator('r2_score')
    @classmethod
    def validate_r2(cls, v):
        if v < -100:
            raise ValueError(f"R² score {v} is suspiciously low; check data quality")
        return v
    
    @model_validator(mode='after')
    def check_consistency(self):
        """Ensure metrics are consistent."""
        if self.rmse > 0 and self.mae > self.rmse:
            raise ValueError("MAE cannot be greater than RMSE")
        return self


class ForecastPoint(BaseModel):
    """Single forecast point with uncertainty."""
    
    period: int = Field(ge=1)
    date: Optional[datetime] = None
    forecast: float
    lower_bound: float
    upper_bound: float
    confidence_level: float = Field(ge=0.0, le=1.0)
    
    @field_validator('forecast', 'lower_bound', 'upper_bound')
    @classmethod
    def validate_non_negative(cls, v):
        """Ensure non-negative forecasts for count/sales data."""
        return max(0, v)
    
    @model_validator(mode='after')
    def validate_bounds(self):
        """Ensure bounds are consistent."""
        if not (self.lower_bound <= self.forecast <= self.upper_bound):
            # Fix bounds if inconsistent
            self.lower_bound = min(self.lower_bound, self.forecast)
            self.upper_bound = max(self.upper_bound, self.forecast)
        return self


class ForecastResult(BaseModel):
    """Complete forecast result."""
    
    model_name: str
    status: Literal["success", "warning", "failed"]
    forecast_points: List[ForecastPoint]
    metrics: ModelMetrics
    data_quality: DataQualityMetrics
    warnings: List[str] = []
    feature_importance: Optional[Dict[str, float]] = None
    shap_values: Optional[Dict[str, Any]] = None
    
    @field_validator('forecast_points')
    @classmethod
    def validate_no_zeros(cls, v):
        """Check for zero forecasts."""
        zero_count = sum(1 for p in v if p.forecast == 0)
        if zero_count > len(v) * 0.3:
            raise ValueError(f"Too many zero forecasts ({zero_count}/{len(v)})")
        return v


class EnsembleForecastResult(BaseModel):
    """Ensemble forecast combining multiple models."""
    
    ensemble_forecast: List[ForecastPoint]
    individual_models: Dict[str, ForecastResult]
    weights: Dict[str, float]
    best_model: str
    ensemble_metrics: ModelMetrics
    
    @field_validator('weights')
    @classmethod
    def validate_weights_sum(cls, v):
        """Ensure weights sum to 1.0."""
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights sum to {total}, not 1.0")
        return v


class TimeSeriesData(BaseModel):
    """Validated time-series data."""
    
    dates: List[datetime]
    values: List[float]
    column_name: str
    frequency: Literal["D", "W", "M", "Q", "Y"]
    
    @field_validator('values')
    @classmethod
    def validate_same_length(cls, v, info):
        if 'dates' in info.data and len(v) != len(info.data['dates']):
            raise ValueError("Dates and values must have same length")
        return v
    
    @field_validator('values')
    @classmethod
    def validate_no_inf(cls, v):
        """Remove inf values."""
        if any(np.isinf(val) for val in v):
            raise ValueError("Data contains infinite values")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
