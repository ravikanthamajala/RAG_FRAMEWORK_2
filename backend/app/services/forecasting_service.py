"""
Machine Learning Forecasting Service with Accuracy Metrics

Integrates data extraction with Prophet, ARIMA, and XGBoost models.
Provides comprehensive accuracy evaluation (MAE, RMSE, MAPE, R²).
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None


class ForecastingService:
    """Advanced forecasting with accuracy metrics."""

    def __init__(self):
        """Initialize forecasting service."""
        self.models_trained = {}
        self.metrics = {}

    @staticmethod
    def _detect_frequency(df: pd.DataFrame) -> str:
        """Detect frequency based on median date differences."""
        if df is None or len(df) < 3:
            return 'MS'
        diffs = df['ds'].sort_values().diff().dropna().dt.days
        if diffs.empty:
            return 'MS'
        median_days = diffs.median()
        if median_days >= 300:
            return 'YS'
        if 25 <= median_days <= 35:
            return 'MS'
        return 'D'

    @staticmethod
    def _normalize_periods(periods: int, freq: str) -> int:
        """Adjust forecast periods based on detected frequency."""
        if freq == 'YS':
            return max(1, int(round(periods / 12)))
        return periods

    @staticmethod
    def calculate_accuracy_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
        """
        Calculate comprehensive accuracy metrics.

        Args:
            y_true (np.ndarray): Actual values
            y_pred (np.ndarray): Predicted values

        Returns:
            dict: MAE, RMSE, MAPE, R² scores
        """
        # Ensure same length
        min_len = min(len(y_true), len(y_pred))
        y_true = y_true[:min_len]
        y_pred = y_pred[:min_len]

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if np.all(y_true != 0) else np.nan
        
        # R² Score
        r2 = r2_score(y_true, y_pred)

        return {
            'MAE': round(mae, 4),
            'RMSE': round(rmse, 4),
            'MAPE': round(mape, 2) if not np.isnan(mape) else 'N/A',
            'R2': round(r2, 4),
            'interpretation': ForecastingService._interpret_metrics(mae, mape, r2)
        }

    @staticmethod
    def _interpret_metrics(mae: float, mape: float, r2: float) -> str:
        """Interpret accuracy metrics quality."""
        if r2 < 0:
            return "Poor - Model performs worse than baseline"
        elif r2 < 0.5:
            return "Fair - Model explains < 50% of variance"
        elif r2 < 0.8:
            return "Good - Model explains 50-80% of variance"
        else:
            return "Excellent - Model explains > 80% of variance"

    def forecast_prophet(self, df: pd.DataFrame, periods: int = 36) -> Dict:
        """
        Forecast using Facebook Prophet with accuracy evaluation.

        Args:
            df (pd.DataFrame): Time series data with 'ds' and 'y' columns
            periods (int): Number of periods to forecast (default 36 months)

        Returns:
            dict: Forecast results, predictions, and accuracy metrics
        """
        try:
            freq = self._detect_frequency(df)
            periods = self._normalize_periods(periods, freq)

            # Split train/test (80/20)
            split_idx = int(len(df) * 0.8)
            train_df = df[:split_idx].copy()
            test_df = df[split_idx:].copy()

            # Train Prophet model
            model = Prophet(
                yearly_seasonality=(freq != 'YS'),
                weekly_seasonality=(freq == 'D'),
                daily_seasonality=False,
                interval_width=0.95
            )
            model.fit(train_df)

            # Evaluate on test set
            test_forecast = model.predict(test_df[['ds']])
            test_metrics = self.calculate_accuracy_metrics(
                test_df['y'].values,
                test_forecast['yhat'].values
            )

            # Generate future forecast
            future = model.make_future_dataframe(periods=periods, freq=freq)
            forecast = model.predict(future)

            self.models_trained['prophet'] = model
            self.metrics['prophet'] = test_metrics

            return {
                'model': 'Prophet',
                'status': 'success',
                'forecast_data': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).to_dict('records'),
                'test_metrics': test_metrics,
                'total_forecast_points': len(forecast),
                'historical_data_points': len(df),
                'forecast_start_date': str(df['ds'].max().date()),
                'forecast_end_date': str(forecast['ds'].iloc[-1].date())
            }

        except Exception as e:
            return {'error': str(e), 'model': 'Prophet', 'status': 'failed'}

    def forecast_arima(self, df: pd.DataFrame, order: Tuple = (1, 1, 1), periods: int = 36) -> Dict:
        """
        Forecast using ARIMA with accuracy evaluation.

        Args:
            df (pd.DataFrame): Time series data with 'y' column
            order (tuple): (p, d, q) parameters
            periods (int): Number of periods to forecast

        Returns:
            dict: ARIMA forecast results and metrics
        """
        try:
            freq = self._detect_frequency(df)
            periods = self._normalize_periods(periods, freq)

            # Split train/test
            split_idx = int(len(df) * 0.8)
            train_data = df['y'].iloc[:split_idx]
            test_data = df['y'].iloc[split_idx:]

            # Train ARIMA model
            model = ARIMA(train_data, order=order)
            fitted_model = model.fit()

            # Evaluate on test set
            test_pred = fitted_model.forecast(steps=len(test_data))
            test_metrics = self.calculate_accuracy_metrics(
                test_data.values,
                test_pred.values
            )

            # Generate future forecast
            forecast_result = fitted_model.get_forecast(steps=periods)
            forecast_df = forecast_result.conf_int(alpha=0.05)
            forecast_df['forecast'] = forecast_result.predicted_mean
            forecast_df['forecast'] = forecast_df['forecast'].clip(lower=0)

            self.models_trained['arima'] = fitted_model
            self.metrics['arima'] = test_metrics

            return {
                'model': 'ARIMA',
                'status': 'success',
                'order': order,
                'forecast_data': [
                    {
                        'period': i,
                        'forecast': float(forecast_df['forecast'].iloc[i]),
                        'lower_bound': float(forecast_df.iloc[i, 0]),
                        'upper_bound': float(forecast_df.iloc[i, 1])
                    }
                    for i in range(len(forecast_df))
                ],
                'test_metrics': test_metrics,
                'forecast_periods': periods,
                'historical_points': len(df)
            }

        except Exception as e:
            return {'error': str(e), 'model': 'ARIMA', 'status': 'failed'}

    def forecast_xgboost(self, df: pd.DataFrame, periods: int = 36, 
                        lag_features: int = 12) -> Dict:
        """
        Forecast using XGBoost with lag features.

        Args:
            df (pd.DataFrame): Time series data with 'y' column
            periods (int): Periods to forecast
            lag_features (int): Number of lag features to use

        Returns:
            dict: XGBoost forecast and metrics
        """
        if XGBRegressor is None:
            return {'error': 'XGBoost not installed', 'status': 'failed'}

        try:
            freq = self._detect_frequency(df)
            periods = self._normalize_periods(periods, freq)

            data = df['y'].values

            if len(data) < lag_features + 5:
                lag_features = max(3, len(data) // 2)

            # Create lag features
            X, y = [], []
            for i in range(lag_features, len(data)):
                X.append(data[i-lag_features:i])
                y.append(data[i])

            X = np.array(X)
            y = np.array(y)

            # Split train/test
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]

            # Train XGBoost
            model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
            model.fit(X_train, y_train)

            # Evaluate
            y_pred_test = model.predict(X_test)
            test_metrics = self.calculate_accuracy_metrics(y_test, y_pred_test)

            # Generate forecasts
            forecast_values = []
            last_sequence = X[-1].copy()

            for _ in range(periods):
                next_pred = model.predict(last_sequence.reshape(1, -1))[0]
                next_pred = max(0, float(next_pred))
                forecast_values.append(float(next_pred))
                last_sequence = np.append(last_sequence[1:], next_pred)

            self.models_trained['xgboost'] = model
            self.metrics['xgboost'] = test_metrics

            return {
                'model': 'XGBoost',
                'status': 'success',
                'lag_features': lag_features,
                'forecast_data': forecast_values,
                'test_metrics': test_metrics,
                'forecast_periods': periods,
                'historical_points': len(df)
            }

        except Exception as e:
            return {'error': str(e), 'model': 'XGBoost', 'status': 'failed'}

    def compare_models(self, df: pd.DataFrame, periods: int = 36) -> Dict:
        """
        Train and compare all available models.

        Args:
            df (pd.DataFrame): Time series data
            periods (int): Forecast periods

        Returns:
            dict: Comparison of all models with accuracy metrics
        """
        results = {
            'comparison': {},
            'best_model': None,
            'best_r2': -np.inf,
            'timestamp': datetime.now().isoformat()
        }

        # Prophet
        prophet_result = self.forecast_prophet(df, periods)
        if prophet_result.get('status') == 'success':
            results['comparison']['prophet'] = prophet_result
            if 'R2' in prophet_result['test_metrics']:
                r2 = prophet_result['test_metrics']['R2']
                if r2 > results['best_r2']:
                    results['best_r2'] = r2
                    results['best_model'] = 'Prophet'

        # ARIMA
        arima_result = self.forecast_arima(df, periods=periods)
        if arima_result.get('status') == 'success':
            results['comparison']['arima'] = arima_result
            if 'R2' in arima_result['test_metrics']:
                r2 = arima_result['test_metrics']['R2']
                if r2 > results['best_r2']:
                    results['best_r2'] = r2
                    results['best_model'] = 'ARIMA'

        # XGBoost
        if XGBRegressor is not None:
            xgb_result = self.forecast_xgboost(df, periods=periods)
            if xgb_result.get('status') == 'success':
                results['comparison']['xgboost'] = xgb_result
                if 'R2' in xgb_result['test_metrics']:
                    r2 = xgb_result['test_metrics']['R2']
                    if r2 > results['best_r2']:
                        results['best_r2'] = r2
                        results['best_model'] = 'XGBoost'

        return results
