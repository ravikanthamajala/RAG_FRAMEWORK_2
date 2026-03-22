# ML Forecasting Integration - API Documentation

## Overview

Your project now has **integrated ML forecasting** that automatically:
1. Processes uploaded Excel/PDF files
2. Extracts numerical data from tables and text
3. Trains 3 forecasting models (Prophet, ARIMA, XGBoost)
4. Evaluates accuracy with multiple metrics
5. Returns the best model with predictions

## Key Improvements Made

### 1. **Data Extraction Pipeline** (`app/utils/data_extractor.py`)
- Extracts structured tables from Excel files
- Extracts numerical patterns from PDFs
- Auto-detects time series candidates
- Provides statistical summaries

### 2. **ML Forecasting Service** (`app/services/forecasting_service.py`)
- **Prophet Model**: Handles seasonality and trends (Facebook's algorithm)
- **ARIMA Model**: Classical statistical forecasting
- **XGBoost Model**: Gradient boosting with lag features
- **Automatic Model Selection**: Compares all 3 and returns the best

### 3. **Accuracy Metrics** (Built-in)

Each model returns 4 accuracy scores:

| Metric | Formula | Interpretation |
|--------|---------|-----------------|
| **MAE** | Mean Absolute Error | Lower = Better (avg prediction error) |
| **RMSE** | Root Mean Squared Error | Penalizes large errors more |
| **MAPE** | Mean Absolute % Error | Percentage error (0-100%) |
| **R²** | Coefficient of Determination | 0 = Bad, 1 = Perfect (% variance explained) |

### 4. **New API Endpoints**

#### POST `/api/upload-and-forecast`
Upload file + automatically forecast + return metrics

**Request:**
```json
{
  "files": [file],
  "forecast_periods": 36,
  "auto_select": true
}
```

**Response:**
```json
{
  "documents": [{
    "filename": "sales_data.xlsx",
    "status": "success",
    "extraction": {
      "sheets": ["Sales", "Forecast"],
      "time_series_candidates": [{
        "sheet": "Sales",
        "date_column": "Date",
        "value_column": "Units_Sold",
        "data_points": 24,
        "date_range": "2022-01-01 to 2024-01-01"
      }]
    }
  }],
  "forecasts": [{
    "filename": "sales_data.xlsx",
    "data_series": "Units_Sold from Sales",
    "data_points": 24,
    "best_model": "Prophet",
    "best_r2_score": 0.8742,
    "models_comparison": {
      "prophet": {
        "test_metrics": {
          "MAE": 150.25,
          "RMSE": 175.43,
          "MAPE": 5.2,
          "R2": 0.8742,
          "interpretation": "Excellent - Model explains > 80% of variance"
        },
        "forecast_data": [...]
      },
      "arima": {
        "test_metrics": { "MAE": 200.5, "RMSE": 220.1, "MAPE": 7.1, "R2": 0.75 },
        ...
      },
      "xgboost": {
        "test_metrics": { "MAE": 180.3, "RMSE": 195.7, "MAPE": 6.5, "R2": 0.82 },
        ...
      }
    }
  }],
  "summary": {
    "files_processed": 1,
    "files_with_forecasts": 1,
    "total_models_trained": 3
  }
}
```

#### POST `/api/extraction-summary`
Quick preview of what data can be extracted (no forecasting)

**Request:**
```json
{
  "file": file
}
```

**Response:**
```json
{
  "filename": "market_data.xlsx",
  "extraction_success": true,
  "summary": {
    "sheets": ["2023_Sales", "2024_Forecast"],
    "numerical_columns": {
      "2023_Sales": {
        "columns": ["Units", "Revenue", "Growth%"],
        "statistics": { ... }
      }
    },
    "time_series_candidates": 2,
    "total_numerical_values": 156
  }
}
```

#### POST `/api/forecast-from-document/<doc_id>`
Re-forecast from existing document with custom parameters

**Query Parameters:**
```
?sheet_name=Sales
&date_column=Date
&value_column=Units
&periods=48
```

## Usage Examples

### Frontend Implementation

```javascript
// In React component
const handleForecast = async (file) => {
  const formData = new FormData();
  formData.append('files', file);
  formData.append('forecast_periods', 36);

  const response = await fetch('http://localhost:5000/api/upload-and-forecast', {
    method: 'POST',
    body: formData,
  });

  const data = await response.json();
  
  // Access results
  console.log(`Best Model: ${data.forecasts[0].best_model}`);
  console.log(`Accuracy (R²): ${data.forecasts[0].best_r2_score}`);
  console.log(`Models: ${Object.keys(data.forecasts[0].models_comparison)}`);
};
```

### Command Line Test

```bash
# Test with a sample Excel file
curl -X POST http://localhost:5000/api/upload-and-forecast \
  -F "files=@sales_data.xlsx" \
  -F "forecast_periods=36"
```

## How to Interpret Results

### Example Output Analysis

If you see:
```json
{
  "best_model": "Prophet",
  "best_r2_score": 0.85,
  "test_metrics": {
    "MAE": 100,
    "RMSE": 120,
    "MAPE": 4.5,
    "interpretation": "Excellent - Model explains > 80% of variance"
  }
}
```

**Interpretation:**
- ✅ **Prophet is the best choice** (R² = 0.85)
- ✅ **Excellent accuracy** - explains 85% of data variance
- ✅ **Average prediction error is 100 units** (MAE)
- ✅ **4.5% average percentage error** (MAPE)

### When to Use Each Model

| Model | Best For | Strengths |
|-------|----------|-----------|
| **Prophet** | Seasonal data with clear trends | Handles missing data, fast training |
| **ARIMA** | Stationary time series | Classical, interpretable, fewer parameters |
| **XGBoost** | Complex patterns with external features | High accuracy, handles non-linearity |

## Data Format Requirements

### Excel Files
Required columns:
- **Date column** (DateTime format)
- **Numeric column** (Numbers to forecast)

Example:
```
Date        | Sales  | Costs
2023-01-01  | 50000  | 30000
2023-02-01  | 52000  | 31000
2023-03-01  | 55000  | 32500
```

Minimum data points: **5** (recommended: **20+**)

### PDF Files
Looks for:
- Numbers and percentages
- Date patterns (YYYY-MM-DD, MM/DD/YYYY)
- Growth indicators ("increased by 10%", etc.)

## Troubleshooting

### No Time Series Found
- Ensure Excel has a Date column and numeric columns
- Date must be in recognized format (YYYY-MM-DD, MM/DD/YYYY, etc.)
- Need at least 5 data points

### Low R² Score (< 0.5)
- **Cause**: Data too noisy or non-linear
- **Solution**: 
  - Check data quality (remove outliers)
  - Use longer historical data
  - Try XGBoost which handles non-linearity better

### Forecasting Failed
- Check file is valid Excel/PDF
- Verify numeric columns have no text mixed in
- Check file isn't corrupted

## Integration Points

### Current Integration
1. ✅ Document Upload (`/api/upload`) → Standard RAG
2. ✅ Smart Upload (`/api/upload-and-forecast`) → **NEW ML Forecasting**
3. ✅ Query Documents (`/api/query`) → Standard RAG
4. ✅ Forecasting Results → Display in UI

### Next Steps (Optional Enhancements)
- Add forecast visualization (charts in UI)
- Store forecasts in MongoDB for history
- Create comparison reports across files
- Export forecasts to CSV/Excel
- Set up automated reforecasting on schedule

## Files Added/Modified

### New Files
- `backend/app/utils/data_extractor.py` - Numerical data extraction
- `backend/app/services/forecasting_service.py` - ML forecasting engine
- `backend/app/routes/smart_upload.py` - New API endpoints
- `frontend/components/SmartUploadForecast.js` - New UI component

### Modified Files
- `backend/app/__init__.py` - Registered new routes
- `frontend/pages/index.js` - Added forecasting tab
- `backend/requirements.txt` - All dependencies already present

## Testing Your Implementation

1. **Start backend**
   ```bash
   cd backend
   python run.py
   ```

2. **Start frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test in browser**
   - Go to `http://localhost:3000`
   - Click "📊 ML Forecasting" tab
   - Upload your Excel file with sales/market data
   - See forecasts with accuracy metrics!

## Performance Notes

- **Fast Models**: Prophet & ARIMA train in seconds
- **Slower Models**: XGBoost takes 1-5 seconds (more accurate)
- **Data Size**: Works with 5-10,000 data points
- **Forecast Length**: 3 years (36 months) is recommended
