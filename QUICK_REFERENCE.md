# Quick Reference Guide - Production System

## System Status
```
✓ Backend:  http://localhost:5000 (Flask)
✓ Frontend: http://localhost:3000 (Next.js)
✓ Date: January 31, 2026
```

## Start System
```bash
# Terminal 1: Backend
cd backend && python run.py

# Terminal 2: Frontend  
cd frontend && npm run dev
```

## Key Components

### 1. Pydantic Validation
- **File:** `backend/app/schemas/forecast.py`
- **Classes:** 7 validation schemas
- **Validates:** R² > -100, bounds consistency, non-negative forecasts

### 2. Production Forecasting
- **File:** `backend/app/services/forecasting_service_v2.py`
- **Methods:** Data quality, preprocessing, feature engineering, ensemble
- **Features:** 27+ engineered features
- **Models:** Prophet + ARIMA + XGBoost

### 3. Backend Routes
- **File:** `backend/app/routes/smart_upload.py`
- **Endpoint:** POST /upload-and-forecast
- **Returns:** Ensemble forecast + individual results + data quality

### 4. Frontend Display
- **File:** `frontend/components/ForecastVisualization.js`
- **Shows:** Chart, quality badge, R² score, ensemble info

## Data Quality Score

```
1.0  ━━━━━━━━━━━━━━━━  Perfect data
0.7  ━━━━━━━━━━  Acceptable
0.3  ━━━  Poor (rejected)
0.0  ━  Unusable
```

## Forecast Data Flow

```
Upload File
    ↓
Extract + Quality Check (0-1 score)
    ↓
Reject if < 0.3
    ↓
Preprocess (fill gaps, remove outliers)
    ↓
Engineer Features (27+)
    ↓
Train Ensemble
  ├─ Prophet
  ├─ ARIMA
  └─ XGBoost
    ↓
Walk-Forward Validation
    ↓
Weight by R² Score
    ↓
Return Results + Display
```

## API Response Format

```json
{
  "ensemble": {
    "best_model": "xgboost",
    "weights": {"prophet": 0.25, "arima": 0.25, "xgboost": 0.5},
    "forecast_data": [
      {"period": 1, "forecast": 2500, "lower_bound": 2300, "upper_bound": 2700}
    ],
    "metrics": {"r2_score": 0.892, "mae": 150, "rmse": 200}
  },
  "data_quality": {
    "quality_score": 0.87,
    "trend_direction": "increasing",
    "seasonality_detected": true
  }
}
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Zero forecasts | Poor data quality | Check data > 12 points |
| Negative R² | Low quality / overfitting | Use walk-forward validation |
| Bounds invalid | Model failure | Pydantic catches this |
| Slow response | Large dataset | Limit to 1000 points |

## Key Metrics

| Metric | Acceptable | Ideal |
|--------|-----------|-------|
| Data Quality | > 0.3 | > 0.7 |
| R² Score | > 0.5 | 0.7-0.95 |
| Zero Forecasts | 0% | 0% |
| Ensemble Weights | Sum to 1.0 | Balanced |

## Feature Engineering (27+ Features)

```
Lag Features:        1, 3, 6, 12 periods
Rolling Stats:       mean, std, min, max (3, 6, 12 windows)
Time Features:       day, month, quarter, year
Cyclical Encoding:   month sine/cosine
Growth Metrics:      % change, MA crossover
```

## Validation Rules

✓ R² > -100 (rejects broken models)  
✓ lower_bound ≤ forecast ≤ upper_bound  
✓ Non-negative forecasts (for count/sales)  
✓ <30% zero forecasts (flags if more)  
✓ Ensemble weights sum to 1.0  

## Installation (Optional Dependencies)

```bash
# For XGBoost + SHAP
pip install xgboost shap

# For async tasks
pip install celery redis
```

## Test System

```bash
cd backend
python test_production_system.py
```

Expected output:
```
TEST 1: DATA QUALITY ASSESSMENT [PASS]
TEST 2: FEATURE ENGINEERING [PASS]
TEST 3: ENSEMBLE FORECASTING [PASS]
TEST 4: PYDANTIC VALIDATION [PASS]
```

## Success Indicators

✓ Data quality score between 0-1  
✓ R² score between -5 and 1  
✓ Forecast bounds logically consistent  
✓ No zero forecasts (0%)  
✓ Ensemble weights sum exactly to 1.0  
✓ Frontend displays results properly  
✓ Confidence intervals shown (95%)  

## Logs & Debugging

```bash
# Backend logs
python run.py 2>&1 | grep -i error

# Frontend console
Open http://localhost:3000 → F12 → Console

# Check data quality
curl -X POST http://localhost:5000/extraction-summary \
  -F "file=@data.csv"
```

## Production Checklist

- [ ] Test with 10+ datasets
- [ ] Verify R² distributions
- [ ] Monitor error rates
- [ ] Setup automated backups
- [ ] Configure monitoring/alerts
- [ ] Document known issues
- [ ] Train users
- [ ] Performance benchmark

## Quick Stats

- **Models Combined:** 3 (Prophet, ARIMA, XGBoost)
- **Features Generated:** 27+
- **Validation Method:** Walk-forward (3-way)
- **Confidence Level:** 95%
- **Data Quality Scoring:** 0-1 (0.3 threshold)
- **R² Validation:** > -100
- **Forecast Horizon:** Up to 120 periods

## Support

For issues:
1. Check backend is running: `http://localhost:5000/health`
2. Check frontend: `http://localhost:3000`
3. Verify data has >12 points
4. Check data quality score > 0.7
5. Review logs for errors

---

**Production-Ready System**  
January 31, 2026
