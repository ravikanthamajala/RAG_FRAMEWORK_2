# Quick Setup Guide

## Project: China's Automotive Dominance - Strategic Analysis for Indian OEMs

### ✅ What's Been Updated

Your backend has been completely aligned with the **Automotive Market Analysis** theme:

1. **Updated Docstrings & Headers** in all backend files
2. **Enhanced RAG Agent Prompt** - Now specialized for automotive market analysis
3. **New Forecasting Agent** - Time series predictions (Prophet, ARIMA, XGBoost)
4. **New Policy Analyzer** - Extract and compare China-India policies
5. **New Analysis Routes** - Market forecasting, policy analysis, OEM strategy endpoints
6. **Complete Architecture Documentation** - See ARCHITECTURE.md

---

## System Architecture Overview

### Three Main Analysis Layers

```
Input Documents (PDFs + Excel)
        ↓
    [RAG Agent]
    - Reads & understands documents
    - Extracts key information
        ↓
    [Analysis Agents]
    ├── Policy Analyzer → Policy insights
    ├── Market Forecaster → Future predictions
    └── Strategy Recommender → OEM strategies
        ↓
    [Output]
    - Market forecasts (3-5 years)
    - Policy recommendations
    - Strategic insights for Indian OEMs
```

---

## New Features Added

### 1. **Market Forecasting** (`/api/forecast/*`)
- Forecasts India's automotive market growth
- Predicts EV adoption rates
- Projects OEM market share changes
- **Models Used**: Prophet, ARIMA, XGBoost

### 2. **Policy Analysis** (`/api/policy/*`)
- Extracts policies from documents
- Compares China vs India policies
- Identifies policy gaps
- Generates recommendations

### 3. **Strategic Insights** (`/api/insights/*`)
- Key market trends
- India vs China metrics
- Strategic focus areas
- Risk & opportunity analysis

---

## Files Created/Modified

### Created:
- ✅ `backend/app/agents/market_forecaster.py` - Forecasting models
- ✅ `backend/app/agents/policy_analyzer.py` - Policy analysis
- ✅ `backend/app/routes/analysis.py` - New API endpoints
- ✅ `ARCHITECTURE.md` - Complete documentation

### Updated:
- ✅ `backend/run.py` - Project description
- ✅ `backend/app/__init__.py` - Registered analysis routes
- ✅ `backend/app/agents/rag_agent.py` - Automotive-focused prompt
- ✅ `backend/app/routes/query.py` - Automotive context
- ✅ `backend/app/routes/upload.py` - Automotive data focus
- ✅ `backend/app/utils/document_processor.py` - Automotive context
- ✅ `backend/requirements.txt` - All dependencies included

---

## How to Use

### Step 1: Organize Your Data
```
Create this folder structure and add your documents:

data/
├── raw/
│   ├── china/
│   │   ├── policies/          → Put China PDFs here
│   │   ├── market_data/       → Put China Excel here
│   │   └── oem_performance/   → Put OEM data here
│   └── india/
│       ├── regulations/       → Put India PDFs here
│       └── market_data/       → Put India Excel here
```

### Step 2: Upload Documents
```
POST /api/upload
- Upload your China market research PDFs
- Upload market data Excel files
```

### Step 3: Query for Insights
```
POST /api/query
{
  "query": "What EV policies should India adopt from China?"
}
```

### Step 4: Get Forecasts
```
POST /api/forecast/market
{
  "data": [...your historical market data...],
  "forecast_periods": 36  // 3 years
}
```

### Step 5: Compare Policies
```
POST /api/policy/compare
{
  "china_policies": {...extracted policies...},
  "india_policies": {...extracted policies...}
}
```

---

## Key Concepts Explained

### **Policy Domains Analyzed**
1. **EV Incentives** - Subsidies and tax credits
2. **Manufacturing** - Local production requirements
3. **Environmental** - Emissions and fuel efficiency standards
4. **Trade** - Import duties and tariffs
5. **R&D** - Research funding and technology development

### **Forecasting Models**
- **Prophet** - Facebook's time series with seasonality
- **ARIMA** - Classical statistical forecasting
- **XGBoost** - Machine learning ensemble method
- **Ensemble** - Combined predictions for best accuracy

### **Market Metrics**
- Total vehicle sales growth
- EV market penetration
- OEM market share
- Manufacturing capacity
- Consumer trends

---

## Next Steps

1. **Test the API**
   ```bash
   cd backend
   python run.py  # Backend runs on localhost:5000
   cd ../frontend
   npm run dev    # Frontend runs on localhost:3000
   ```

2. **Upload sample market data**
   - Find China automotive market reports
   - Find India market statistics
   - Upload via the frontend or API

3. **Run analysis queries**
   - Ask about policy impacts
   - Request market forecasts
   - Get OEM strategy recommendations

4. **Review insights**
   - Check policy comparison results
   - Analyze forecast confidence
   - Review strategic recommendations

---

## Expected Output Examples

### Policy Analysis Output
```json
{
  "china_leading_policies": ["EV_Subsidies", "Local_Content_Requirements"],
  "india_gaps": ["EV_Charging_Infrastructure", "Tax_Incentives"],
  "alignment_score": 35,
  "recommendations": ["Adopt EV subsidy programs", "Build charging network"]
}
```

### Market Forecast Output
```json
{
  "model": "Prophet",
  "forecast_2025": 3500000,  // vehicles
  "forecast_2026": 4100000,
  "forecast_2027": 4850000,
  "ev_penetration_2027": "15-18%",
  "confidence": "High"
}
```

### OEM Strategy Output
```json
{
  "short_term": ["Focus on ICE efficiency", "Prepare EV transition"],
  "medium_term": ["Launch EV models", "Develop local supply chain"],
  "long_term": ["Become tech leader", "Enter autonomous market"],
  "competitive_advantages": ["Cost", "Growing market", "Government support"]
}
```

---

## Troubleshooting

**Q: Documents not processing?**
- Check file formats (PDF or Excel only)
- Ensure MongoDB is running

**Q: Forecast models failing?**
- Need at least 24 months of historical data
- Data should have date and numerical columns

**Q: Policy analysis empty?**
- Upload policy documents first
- Ensure documents contain policy-related keywords

---

## Support

For detailed API documentation, see `ARCHITECTURE.md`
For project theme context, see `README.md`

---

**Your project is now ready for automotive market analysis! 🚗📊**
