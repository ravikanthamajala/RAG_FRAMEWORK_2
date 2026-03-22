"""
Production-Grade Forecasting Service

Fixes:
- Zero forecasts → Better preprocessing + ensemble
- Negative R² → Walk-forward validation + quality checks
- Feature engineering → Lag, rolling, seasonal features
- Probabilistic predictions → Confidence intervals
- SHAP explainability → Model interpretation
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import warnings
import logging
from pandas.tseries.frequencies import to_offset

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

try:
    from xgboost import XGBRegressor
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    XGBRegressor = None
    SHAP_AVAILABLE = False
    logger.warning("XGBoost/SHAP not available")

from app.schemas.forecast import (
    ForecastResult, ModelMetrics, ForecastPoint, 
    DataQualityMetrics, EnsembleForecastResult, TimeSeriesData
)
from app.services.forecast_preprocessing import ForecastPreprocessingPipeline, PreprocessingConfig


class AdvancedForecastingService:
    """Production-grade forecasting with validation and explainability."""

    def __init__(self):
        self.models_trained = {}
        self.scalers = {}
        self.feature_names = []
        self.preprocessing_pipeline = ForecastPreprocessingPipeline(
            PreprocessingConfig(
                date_col='ds',
                target_col='y',
                monthly_freq='MS',
                monthly_aggregation='sum',
                interpolation_method='linear',
                outlier_method='iqr',
                outlier_action='interpolate',
                test_ratio=0.2,
                min_train_points=12,
            )
        )
        
    def assess_data_quality(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Comprehensive data quality assessment."""
        total = len(df)
        missing = df['y'].isna().sum()
        missing_pct = (missing / total) * 100
        
        # Detect outliers (IQR method)
        Q1 = df['y'].quantile(0.25)
        Q3 = df['y'].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df['y'] < (Q1 - 1.5 * IQR)) | (df['y'] > (Q3 + 1.5 * IQR))).sum()
        
        # Date gaps
        df_sorted = df.sort_values('ds')
        date_diffs = df_sorted['ds'].diff()
        median_diff = date_diffs.median()
        gaps = (date_diffs > median_diff * 2).sum()
        
        # Stationarity test
        try:
            adf_result = adfuller(df['y'].dropna())
            stationarity_pvalue = adf_result[1]
        except:
            stationarity_pvalue = 1.0
        
        # Trend detection
        if len(df) > 3:
            trend_coef = np.polyfit(range(len(df)), df['y'].values, 1)[0]
            if abs(trend_coef) < df['y'].std() * 0.01:
                trend = "stable"
            elif trend_coef > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            # Volatility check
            cv = df['y'].std() / df['y'].mean() if df['y'].mean() != 0 else 0
            if cv > 0.5:
                trend = "volatile"
        else:
            trend = "stable"
        
        # Seasonality detection (basic)
        seasonality = len(df) > 24 and df['y'].autocorr(lag=12) > 0.5
        
        return DataQualityMetrics(
            total_points=total,
            missing_values=int(missing),
            missing_percentage=float(missing_pct),
            outliers_detected=int(outliers),
            date_gaps=int(gaps),
            seasonality_detected=bool(seasonality),
            trend_direction=trend,
            stationarity_test_pvalue=float(stationarity_pvalue)
        )
    
    def preprocess_data(self, df: pd.DataFrame, fill_method='interpolate') -> pd.DataFrame:
        """Enhanced data preprocessing."""
        pipeline = ForecastPreprocessingPipeline(
            PreprocessingConfig(
                date_col='ds',
                target_col='y',
                monthly_freq='MS',
                monthly_aggregation='sum',
                interpolation_method='linear' if fill_method == 'interpolate' else 'nearest',
                outlier_method='iqr',
                outlier_action='interpolate',
                test_ratio=0.2,
                min_train_points=12,
            )
        )
        artifacts = pipeline.preprocess_target_series(df)
        self.preprocessing_pipeline = pipeline
        return artifacts.cleaned_df

    @staticmethod
    def _infer_date_offset(df: pd.DataFrame):
        if df is None or len(df) < 2:
            return pd.DateOffset(months=1)
        inferred = pd.infer_freq(pd.to_datetime(df['ds']))
        if inferred:
            return to_offset(inferred)
        return pd.DateOffset(months=1)
    
    def create_features(self, df: pd.DataFrame, lags=[1, 3, 6, 12], rolling_windows=[3, 6, 12]) -> pd.DataFrame:
        """Advanced feature engineering."""
        df = df.copy()
        features = pd.DataFrame(index=df.index)
        
        # Lag features
        for lag in lags:
            features[f'lag_{lag}'] = df['y'].shift(lag)
        
        # Rolling statistics
        for window in rolling_windows:
            features[f'rolling_mean_{window}'] = df['y'].rolling(window=window, min_periods=1).mean()
            features[f'rolling_std_{window}'] = df['y'].rolling(window=window, min_periods=1).std()
            features[f'rolling_min_{window}'] = df['y'].rolling(window=window, min_periods=1).min()
            features[f'rolling_max_{window}'] = df['y'].rolling(window=window, min_periods=1).max()
        
        # Time-based features
        features['day_of_week'] = df['ds'].dt.dayofweek
        features['day_of_month'] = df['ds'].dt.day
        features['month'] = df['ds'].dt.month
        features['quarter'] = df['ds'].dt.quarter
        features['year'] = df['ds'].dt.year
        
        # Cyclical encoding
        features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
        features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
        
        # Growth rate
        features['growth_rate'] = df['y'].pct_change()
        
        # Moving average crossover
        features['ma_short'] = df['y'].rolling(window=3, min_periods=1).mean()
        features['ma_long'] = df['y'].rolling(window=12, min_periods=1).mean()
        features['ma_crossover'] = features['ma_short'] - features['ma_long']
        
        # Fill any remaining NaN with forward fill
        features = features.ffill().fillna(0)
        
        self.feature_names = features.columns.tolist()
        return features
    
    def walk_forward_validation(self, df: pd.DataFrame, model_type='xgboost', 
                                n_splits=3) -> Tuple[List[float], List[float]]:
        """Walk-forward cross-validation."""
        y_true_all = []
        y_pred_all = []
        
        total_size = len(df)
        test_size = total_size // (n_splits + 1)
        
        for i in range(n_splits):
            train_end = total_size - test_size * (n_splits - i)
            test_end = train_end + test_size
            
            train_df = df.iloc[:train_end].copy()
            test_df = df.iloc[train_end:test_end].copy()
            
            if len(train_df) < 12 or len(test_df) < 3:
                continue
            
            try:
                if model_type == 'xgboost':
                    y_pred = self._forecast_xgboost_internal(train_df, len(test_df))
                elif model_type == 'arima':
                    y_pred = self._forecast_arima_internal(train_df, len(test_df))
                else:
                    continue
                
                y_true_all.extend(test_df['y'].values)
                y_pred_all.extend(y_pred[:len(test_df)])
            except Exception as e:
                logger.warning(f"Walk-forward split {i} failed: {e}")
                continue
        
        return y_true_all, y_pred_all
    
    def _forecast_arima_internal(self, df: pd.DataFrame, periods: int) -> np.ndarray:
        """Internal ARIMA forecast helper."""
        try:
            model = ARIMA(df['y'].values, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
            fitted = model.fit()
            forecast = fitted.forecast(steps=periods)
            return np.maximum(0, forecast)  # Clip negatives
        except:
            # Fallback to simpler model
            model = ARIMA(df['y'].values, order=(1, 0, 0))
            fitted = model.fit()
            forecast = fitted.forecast(steps=periods)
            return np.maximum(0, forecast)
    
    def _forecast_xgboost_internal(self, df: pd.DataFrame, periods: int) -> np.ndarray:
        """Internal XGBoost forecast helper."""
        features = self.create_features(df)
        
        # Prepare training data
        X = features.iloc[12:].values  # Skip first 12 due to lags
        y = df['y'].iloc[12:].values
        
        # Train model
        model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
        model.fit(X, y)
        
        # Recursive forecasting
        forecast = []
        last_known = df.copy()
        
        for _ in range(periods):
            # Generate features for next step
            next_features = self.create_features(last_known)
            next_X = next_features.iloc[-1:].values
            
            # Predict
            pred = model.predict(next_X)[0]
            pred = max(0, pred)  # Clip negative
            forecast.append(pred)
            
            # Append prediction for next iteration
            next_date = last_known['ds'].iloc[-1] + self._infer_date_offset(last_known)
            new_row = pd.DataFrame({'ds': [next_date], 'y': [pred]})
            last_known = pd.concat([last_known, new_row], ignore_index=True)
        
        return np.array(forecast)
    
    def forecast_with_validation(self, df: pd.DataFrame, periods: int = 24, 
                                 model_type='auto') -> ForecastResult:
        """Forecast with comprehensive validation."""
        
        # Data quality check
        quality = self.assess_data_quality(df)
        
        if quality.quality_score < 0.3:
            raise ValueError(f"Data quality too low ({quality.quality_score:.2f}). "
                           "Check for missing values, outliers, or gaps.")
        
        # Preprocess
        df_clean = self.preprocess_data(df)
        
        # Choose model
        if model_type == 'auto':
            if len(df_clean) > 50 and XGBRegressor is not None:
                model_type = 'ensemble'
            elif len(df_clean) > 24:
                model_type = 'arima'
            else:
                model_type = 'prophet'
        
        # Walk-forward validation
        y_true, y_pred = self.walk_forward_validation(df_clean, model_type='xgboost', n_splits=3)
        
        if len(y_true) > 0:
            val_metrics = self._calculate_metrics(np.array(y_true), np.array(y_pred))
        else:
            val_metrics = None
        
        # Generate forecast
        if model_type == 'ensemble':
            result = self.forecast_ensemble(df_clean, periods)
            return result
        elif model_type == 'xgboost':
            return self.forecast_xgboost(df_clean, periods, validation_metrics=val_metrics)
        elif model_type == 'arima':
            return self.forecast_arima(df_clean, periods, validation_metrics=val_metrics)
        else:
            return self.forecast_prophet(df_clean, periods, validation_metrics=val_metrics)
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> ModelMetrics:
        """Calculate comprehensive model metrics."""
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # MAPE
        mask = y_true != 0
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = None
        
        # R²
        r2 = r2_score(y_true, y_pred)
        
        # Adjusted R²
        n = len(y_true)
        p = 1  # Simplified
        adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2
        
        return ModelMetrics(
            mae=float(mae),
            rmse=float(rmse),
            mape=float(mape) if mape is not None else None,
            r2_score=float(r2),
            adjusted_r2=float(adj_r2)
        )
    
    def forecast_ensemble(self, df: pd.DataFrame, periods: int = 24) -> EnsembleForecastResult:
        """Ensemble forecast combining multiple models."""
        
        # Train individual models
        models_results = {}
        
        try:
            models_results['prophet'] = self.forecast_prophet(df, periods)
        except Exception as e:
            logger.warning(f"Prophet failed: {e}")
        
        try:
            models_results['arima'] = self.forecast_arima(df, periods)
        except Exception as e:
            logger.warning(f"ARIMA failed: {e}")
        
        if XGBRegressor is not None:
            try:
                models_results['xgboost'] = self.forecast_xgboost(df, periods)
            except Exception as e:
                logger.warning(f"XGBoost failed: {e}")
        
        if len(models_results) == 0:
            raise ValueError("All models failed")
        
        # Calculate weights based on validation R²
        weights = {}
        for name, result in models_results.items():
            r2 = result.metrics.r2_score
            # Convert R² to weight (handle negative R²)
            weight = max(0, r2 + 1) if r2 < 0 else r2
            weights[name] = weight
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            # Equal weights if all R² are negative
            weights = {k: 1.0 / len(weights) for k in weights.keys()}
        
        # Combine forecasts
        ensemble_points = []
        for i in range(periods):
            weighted_forecast = 0
            weighted_lower = 0
            weighted_upper = 0
            
            for name, result in models_results.items():
                if i < len(result.forecast_points):
                    point = result.forecast_points[i]
                    w = weights[name]
                    weighted_forecast += point.forecast * w
                    weighted_lower += point.lower_bound * w
                    weighted_upper += point.upper_bound * w
            
            ensemble_points.append(ForecastPoint(
                period=i + 1,
                forecast=weighted_forecast,
                lower_bound=weighted_lower,
                upper_bound=weighted_upper,
                confidence_level=0.95
            ))
        
        # Best model
        best_model = max(models_results.items(), key=lambda x: x[1].metrics.r2_score)[0]
        
        # Ensemble metrics (use best model's metrics as proxy)
        ensemble_metrics = models_results[best_model].metrics
        
        return EnsembleForecastResult(
            ensemble_forecast=ensemble_points,
            individual_models={k: v for k, v in models_results.items()},
            weights=weights,
            best_model=best_model,
            ensemble_metrics=ensemble_metrics
        )
    
    def forecast_prophet(self, df: pd.DataFrame, periods: int = 24, 
                        validation_metrics: Optional[ModelMetrics] = None) -> ForecastResult:
        """Prophet forecast with validation."""
        quality = self.assess_data_quality(df)
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.95
        )
        model.fit(df)
        
        future = model.make_future_dataframe(periods=periods, freq='D')
        forecast_df = model.predict(future)
        
        # Extract future predictions
        forecast_points = []
        for i in range(periods):
            idx = len(df) + i
            if idx < len(forecast_df):
                row = forecast_df.iloc[idx]
                forecast_points.append(ForecastPoint(
                    period=i + 1,
                    date=row['ds'],
                    forecast=max(0, row['yhat']),
                    lower_bound=max(0, row['yhat_lower']),
                    upper_bound=max(0, row['yhat_upper']),
                    confidence_level=0.95
                ))
        
        # Metrics
        if validation_metrics is None:
            train_pred = forecast_df.iloc[:len(df)]['yhat'].values
            metrics = self._calculate_metrics(df['y'].values, train_pred)
        else:
            metrics = validation_metrics
        
        return ForecastResult(
            model_name="Prophet",
            status="success",
            forecast_points=forecast_points,
            metrics=metrics,
            data_quality=quality,
            warnings=[]
        )
    
    def forecast_arima(self, df: pd.DataFrame, periods: int = 24,
                      validation_metrics: Optional[ModelMetrics] = None) -> ForecastResult:
        """ARIMA forecast with validation."""
        quality = self.assess_data_quality(df)
        
        model = ARIMA(df['y'].values, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
        fitted = model.fit()
        
        forecast_result = fitted.get_forecast(steps=periods)
        forecast_mean = forecast_result.predicted_mean
        forecast_ci = forecast_result.conf_int(alpha=0.05)
        
        forecast_points = []
        for i in range(periods):
            forecast_points.append(ForecastPoint(
                period=i + 1,
                forecast=max(0, float(forecast_mean[i])),
                lower_bound=max(0, float(forecast_ci.iloc[i, 0])),
                upper_bound=max(0, float(forecast_ci.iloc[i, 1])),
                confidence_level=0.95
            ))
        
        # Metrics
        if validation_metrics is None:
            train_pred = fitted.fittedvalues
            metrics = self._calculate_metrics(df['y'].values, train_pred)
        else:
            metrics = validation_metrics
        
        return ForecastResult(
            model_name="ARIMA",
            status="success",
            forecast_points=forecast_points,
            metrics=metrics,
            data_quality=quality,
            warnings=[],
            feature_importance={'order': str(fitted.model.order)}
        )
    
    def forecast_xgboost(self, df: pd.DataFrame, periods: int = 24,
                        validation_metrics: Optional[ModelMetrics] = None) -> ForecastResult:
        """XGBoost forecast with SHAP explainability."""
        if XGBRegressor is None:
            raise ImportError("XGBoost not installed")
        
        quality = self.assess_data_quality(df)
        features = self.create_features(df)
        
        # Prepare data
        X = features.iloc[12:].values
        y = df['y'].iloc[12:].values
        
        # Train
        model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
        model.fit(X, y)
        
        # Recursive forecast
        forecast_values = self._forecast_xgboost_internal(df, periods)
        
        # Calculate confidence intervals (simplified)
        std_error = np.std(y - model.predict(X))
        z_score = 1.96  # 95% confidence
        
        forecast_points = []
        for i, val in enumerate(forecast_values):
            forecast_points.append(ForecastPoint(
                period=i + 1,
                forecast=float(val),
                lower_bound=max(0, float(val - z_score * std_error)),
                upper_bound=float(val + z_score * std_error),
                confidence_level=0.95
            ))
        
        # Feature importance
        feature_importance = dict(zip(self.feature_names, model.feature_importances_))
        feature_importance = {k: float(v) for k, v in sorted(feature_importance.items(), 
                                                             key=lambda x: x[1], reverse=True)[:10]}
        
        # SHAP values
        shap_values_dict = None
        if SHAP_AVAILABLE:
            try:
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X)
                shap_values_dict = {
                    'mean_abs_shap': {name: float(np.abs(shap_values[:, i]).mean()) 
                                     for i, name in enumerate(self.feature_names)}
                }
            except Exception as e:
                logger.warning(f"SHAP calculation failed: {e}")
        
        # Metrics
        if validation_metrics is None:
            train_pred = model.predict(X)
            metrics = self._calculate_metrics(y, train_pred)
        else:
            metrics = validation_metrics
        
        return ForecastResult(
            model_name="XGBoost",
            status="success",
            forecast_points=forecast_points,
            metrics=metrics,
            data_quality=quality,
            warnings=[],
            feature_importance=feature_importance,
            shap_values=shap_values_dict
        )
