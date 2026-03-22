"""
Automotive Market Forecasting Agent

Performs time series forecasting for India's automotive market based on:
- Historical data from Excel files
- China's market trends and policy impacts
- Predictive modeling using Prophet, ARIMA, XGBoost
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.preprocessing import MinMaxScaler
except ImportError:
    # Fallback implementation if sklearn not available
    class MinMaxScaler:
        def __init__(self):
            self.min = None
            self.max = None
        def fit(self, x):
            self.min = np.min(x)
            self.max = np.max(x)
            return self
        def transform(self, x):
            return (x - self.min) / (self.max - self.min)

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None


class AutomotiveMarketForecaster:
    """Forecasts India's automotive market metrics based on historical and policy data."""

    def __init__(self):
        """Initialize the forecaster with preprocessing tools."""
        self.scaler = MinMaxScaler()
        self.forecast_periods = 36  # 3 years monthly forecast

    def prepare_data(self, df, date_column, value_column):
        """
        Prepare data for forecasting.

        Args:
            df (pd.DataFrame): Input data with dates and values
            date_column (str): Column name for dates
            value_column (str): Column name for values to forecast

        Returns:
            pd.DataFrame: Cleaned and formatted data
        """
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])
        df_copy = df_copy.sort_values(date_column)
        df_copy = df_copy.fillna(method='ffill').fillna(method='bfill')

        return df_copy[[date_column, value_column]].rename(columns={
            date_column: 'ds',
            value_column: 'y'
        })

    def forecast_prophet(self, df, periods=36):
        """
        Forecast using Facebook Prophet.

        Args:
            df (pd.DataFrame): Time series data with 'ds' and 'y' columns
            periods (int): Number of periods to forecast

        Returns:
            dict: Forecast results with upper and lower bounds
        """
        try:
            model = Prophet(yearly_seasonality=True, interval_width=0.95)
            model.fit(df)

            future = model.make_future_dataframe(periods=periods, freq='M')
            forecast = model.predict(future)

            return {
                'model': 'Prophet',
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
                'mape': self._calculate_mape(df['y'].values, forecast['yhat'].values[:len(df)])
            }
        except Exception as e:
            return {'error': str(e), 'model': 'Prophet'}

    def forecast_arima(self, df, order=(1, 1, 1), periods=36):
        """
        Forecast using ARIMA model.

        Args:
            df (pd.DataFrame): Time series data with 'y' column
            order (tuple): ARIMA order (p, d, q)
            periods (int): Number of periods to forecast

        Returns:
            dict: ARIMA forecast results
        """
        try:
            model = ARIMA(df['y'], order=order)
            fitted = model.fit()
            forecast = fitted.get_forecast(steps=periods)

            forecast_df = pd.DataFrame({
                'forecast': forecast.predicted_mean.values,
                'lower_bound': forecast.conf_int().iloc[:, 0].values,
                'upper_bound': forecast.conf_int().iloc[:, 1].values
            })

            return {
                'model': 'ARIMA',
                'order': order,
                'forecast': forecast_df.to_dict('records'),
                'aic': fitted.aic
            }
        except Exception as e:
            return {'error': str(e), 'model': 'ARIMA'}

    def forecast_xgboost(self, df, lags=12, periods=36):
        """
        Forecast using XGBoost with lagged features.

        Args:
            df (pd.DataFrame): Time series data with 'y' column
            lags (int): Number of lags for features
            periods (int): Number of periods to forecast

        Returns:
            dict: XGBoost forecast results
        """
        if XGBRegressor is None:
            return {'error': 'XGBoost not installed', 'model': 'XGBoost', 'status': 'skipped'}
        
        try:
            # Create lagged features
            data = df['y'].values
            X, y = [], []

            for i in range(lags, len(data)):
                X.append(data[i-lags:i])
                y.append(data[i])

            X = np.array(X)
            y = np.array(y)

            # Train model
            model = XGBRegressor(n_estimators=100, max_depth=5, random_state=42)
            model.fit(X, y)

            # Generate forecast
            last_sequence = data[-lags:]
            forecast_values = []

            for _ in range(periods):
                pred = model.predict(last_sequence.reshape(1, -1))[0]
                forecast_values.append(pred)
                last_sequence = np.append(last_sequence[1:], pred)

            return {
                'model': 'XGBoost',
                'forecast': forecast_values,
                'feature_importance': dict(zip(range(lags), model.feature_importances_))
            }
        except Exception as e:
            return {'error': str(e), 'model': 'XGBoost'}

    def _calculate_mape(self, actual, predicted):
        """Calculate Mean Absolute Percentage Error."""
        return np.mean(np.abs((actual - predicted) / actual)) * 100

    def generate_ensemble_forecast(self, df, periods=36):
        """
        Generate ensemble forecast combining multiple models.

        Args:
            df (pd.DataFrame): Time series data
            periods (int): Number of periods to forecast

        Returns:
            dict: Ensemble forecast with model weights
        """
        prophet_result = self.forecast_prophet(df, periods)
        arima_result = self.forecast_arima(df, periods=periods)
        xgb_result = self.forecast_xgboost(df, periods=periods)

        ensemble = {
            'models': [prophet_result, arima_result, xgb_result],
            'forecast_date': datetime.now().isoformat(),
            'periods': periods,
            'recommendation': self._select_best_model([prophet_result, arima_result, xgb_result])
        }

        return ensemble

    def _select_best_model(self, results):
        """Select best performing model."""
        scores = {}
        for result in results:
            if 'error' not in result:
                if result['model'] == 'Prophet' and 'mape' in result:
                    scores[result['model']] = result['mape']
                elif result['model'] == 'ARIMA' and 'aic' in result:
                    scores[result['model']] = result['aic']

        if scores:
            return min(scores, key=scores.get)
        return 'Ensemble (combined weights)'

    def forecast_oem_market_share(self, df, oem_data):
        """
        Forecast market share evolution for OEMs.

        Args:
            df (pd.DataFrame): Historical market data
            oem_data (dict): OEM-specific data

        Returns:
            dict: OEM market share forecasts
        """
        oem_forecasts = {}

        for oem, oem_df in oem_data.items():
            try:
                forecast_result = self.forecast_prophet(
                    self.prepare_data(oem_df, 'date', 'market_share'),
                    periods=self.forecast_periods
                )
                oem_forecasts[oem] = forecast_result
            except Exception as e:
                oem_forecasts[oem] = {'error': str(e)}

        return oem_forecasts

    def forecast_ev_adoption(self, historical_ev_data):
        """
        Forecast EV adoption rates in India.

        Args:
            historical_ev_data (pd.DataFrame): Historical EV sales/adoption data

        Returns:
            dict: EV adoption forecast
        """
        try:
            df = self.prepare_data(historical_ev_data, 'date', 'ev_percentage')
            forecast = self.forecast_prophet(df, self.forecast_periods)

            return {
                'metric': 'EV_Adoption_Rate',
                'forecast': forecast,
                'insights': [
                    'Monitor inflection points in EV adoption',
                    'Compare with China\'s adoption trajectory',
                    'Identify policy intervention opportunities'
                ]
            }
        except Exception as e:
            return {'error': str(e), 'metric': 'EV_Adoption_Rate'}
