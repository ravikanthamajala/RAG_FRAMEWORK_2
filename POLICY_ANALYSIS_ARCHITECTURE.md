# 🏗️ Policy Analysis System Architecture

## Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js/React)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────┐         ┌──────────────────────────┐          │
│  │  SmartUploadForecast     │         │  ForecastInsights (Q&A)  │          │
│  │  - Upload documents      │         │  - Ask questions         │          │
│  │  - Set forecast target   │         │  - Get intelligent       │          │
│  │  - View results          │         │    answers               │          │
│  └────────────┬─────────────┘         └──────────┬───────────────┘          │
│               │                                   │                          │
│               │ POST /api/upload-and-forecast     │ POST /api/forecast-     │
│               │ + policy analysis                 │       insights/ask      │
│               │                                   │                          │
│               ▼                                   ▼                          │
│  ┌──────────────────────────┐         ┌──────────────────────────┐          │
│  │ ForecastVisualization    │         │  PolicyInsights          │          │
│  │ - Charts & metrics       │         │  - Timeline chart        │          │
│  │ - Model comparison       │         │  - Contribution chart    │          │
│  │ - Forecast insights      │         │  - Roadmap chart         │          │
│  │ - Data quality           │         │  - Gap analysis chart    │          │
│  └──────────────────────────┘         │  - Recommendations       │          │
│                                       │  - Forward strategy      │          │
│                                       └──────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │
                HTTP REST API (Port 5000)
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (Flask/Python)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              /api/upload-and-forecast Route                          │   │
│  │  ┌─────────────────────────────────────────────────────────┐        │   │
│  │  │ 1. File Processing (PDF/XLSX/CSV)                      │        │   │
│  │  │    └─ process_document()                               │        │   │
│  │  ├─────────────────────────────────────────────────────────┤        │   │
│  │  │ 2. Data Extraction                                      │        │   │
│  │  │    └─ DataExtractor.extract_numeric_series()           │        │   │
│  │  ├─────────────────────────────────────────────────────────┤        │   │
│  │  │ 3. Forecasting (Ensemble)                              │        │   │
│  │  │    ├─ Prophet                                           │        │   │
│  │  │    ├─ ARIMA                                             │        │   │
│  │  │    └─ XGBoost                                           │        │   │
│  │  │    └─ Ensemble (weighted average)                       │        │   │
│  │  ├─────────────────────────────────────────────────────────┤        │   │
│  │  │ 4. POLICY ANALYSIS (NEW)                               │        │   │
│  │  │    └─ PolicyAnalyzer                                   │        │   │
│  │  │       ├─ Extract document context                      │        │   │
│  │  │       └─ analyze_comprehensive_policy_impact()         │        │   │
│  │  │          └─ LLM (DeepSeek R1)                          │        │   │
│  │  ├─────────────────────────────────────────────────────────┤        │   │
│  │  │ 5. VISUALIZATION (NEW)                                 │        │   │
│  │  │    └─ PolicyVisualizer                                 │        │   │
│  │  │       ├─ create_policy_adoption_timeline()             │        │   │
│  │  │       ├─ create_contribution_waterfall()               │        │   │
│  │  │       ├─ create_strategic_roadmap()                    │        │   │
│  │  │       └─ create_policy_gap_analysis()                  │        │   │
│  │  │                                                         │        │   │
│  │  │  Returns all as Base64 PNG images                      │        │   │
│  │  ├─────────────────────────────────────────────────────────┤        │   │
│  │  │ 6. Response Assembly                                   │        │   │
│  │  │    ├─ forecasts: [...]                                 │        │   │
│  │  │    ├─ policy_insights: {                               │        │   │
│  │  │    │  ├─ policies_adopted_from_china                   │        │   │
│  │  │    │  ├─ policy_contribution_breakdown                 │        │   │
│  │  │    │  ├─ policy_gaps                                   │        │   │
│  │  │    │  ├─ strategic_recommendations                     │        │   │
│  │  │    │  └─ forward_strategy                              │        │   │
│  │  │    └─ policy_charts: [{                                │        │   │
│  │  │       ├─ timeline chart (PNG)                          │        │   │
│  │  │       ├─ waterfall chart (PNG)                         │        │   │
│  │  │       ├─ roadmap chart (PNG)                           │        │   │
│  │  │       └─ gap analysis chart (PNG)                      │        │   │
│  │  │    }]                                                  │        │   │
│  │  └─────────────────────────────────────────────────────────┘        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │          /api/forecast-insights/ask Route (Optional Q&A)            │   │
│  │  ┌─────────────────────────────────────────────────────────┐        │   │
│  │  │ 1. Accept forecast data + question                      │        │   │
│  │  │ 2. ForecastInsightsAgent                                │        │   │
│  │  │    ├─ Build forecast context                            │        │   │
│  │  │    └─ Query LLM with specialized prompt                 │        │   │
│  │  │ 3. Extract insights & metrics                           │        │   │
│  │  │ 4. Return answer + confidence                           │        │   │
│  │  └─────────────────────────────────────────────────────────┘        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │
                      (Integration Point)
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────┐       ┌──────────────────────────┐            │
│  │  Ollama (Local)          │       │  Matplotlib/Seaborn      │            │
│  │  LLM: DeepSeek R1:14b    │       │  Visualization Engine    │            │
│  │  ✓ Policy analysis       │       │  ✓ Timeline charts       │            │
│  │  ✓ Context extraction    │       │  ✓ Waterfall diagrams    │            │
│  │  ✓ Recommendations       │       │  ✓ Gantt charts          │            │
│  │  ✓ Fallback data         │       │  ✓ Gap analysis          │            │
│  └──────────────────────────┘       └──────────────────────────┘            │
│                                                                               │
│  ┌──────────────────────────┐       ┌──────────────────────────┐            │
│  │  MongoDB                 │       │  Pandas/NumPy            │            │
│  │  (Optional Document DB)  │       │  (Data Processing)       │            │
│  │  ✓ Store documents       │       │  ✓ DataFrame operations  │            │
│  │  ✓ Cache results         │       │  ✓ Calculations          │            │
│  │  ✓ Track uploads         │       │  ✓ Metrics extraction    │            │
│  └──────────────────────────┘       └──────────────────────────┘            │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Complete Process

```
┌─────────────┐
│   User      │
│  Uploads    │
│  File       │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────┐
│  File Processing             │
│  └─ Extract text from        │
│     PDF/XLSX/CSV             │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Data Extraction             │
│  └─ Find numeric series      │
│  └─ Parse dates              │
│  └─ Validate timeseries      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  ML Forecasting              │
│  ├─ Train Prophet            │
│  ├─ Train ARIMA              │
│  ├─ Train XGBoost            │
│  └─ Create Ensemble          │
└──────────┬───────────────────┘
           │
           ├─────────────┬────────────────────┬──────────────────┐
           │             │                    │                  │
           ▼             ▼                    ▼                  ▼
    ┌──────────┐  ┌────────────┐  ┌─────────────────┐  ┌─────────────┐
    │Forecasts │  │ Document   │  │ Policy Analysis │  │ Visualization
    │with      │  │ Context    │  │ Triggered!      │  │ Generation
    │Metrics   │  │ Extracted  │  │                 │  │
    └─────┬────┘  └──────┬─────┘  └────────┬────────┘  │
          │               │                 │           │
          │               │                 ▼           │
          │               │        ┌───────────────────┐│
          │               │        │ PolicyAnalyzer    ││
          │               └───────►├─ Extract context  ││
          │                        │ - Query LLM       ││
          │                        │ - Generate        ││
          │                        │   insights        ││
          │                        └─────┬─────────────┘│
          │                              │              │
          │                              ▼              │
          │                      ┌──────────────────┐   │
          │                      │ Policy Insights: │   │
          │                      │ - Adoption data  │   │
          │                      │ - Contribution % │   │
          │                      │ - Gaps           │   │
          │                      │ - Recommendations
          │                      │ - Forward plan   │   │
          │                      └──────┬───────────┤   │
          │                             │           │   │
          │                             │           ▼   │
          │                             │   ┌──────────┐│
          │                             │   │PolicyVisua-
          │                             │   │lizer     ││
          │                             │   │- Timeline ││
          │                             │   │- Waterfall││
          │                             │   │- Roadmap  ││
          │                             │   │- Gap Chart││
          │                             │   └──────┬────┘
          │                             │          │
          │                             │          ▼
          │                             │   ┌──────────┐
          │                             │   │ 4 PNG    │
          │                             │   │ Charts   │
          │                             │   │ (Base64) │
          │                             │   └────┬─────┘
          │                             │        │
          └─────────────────────┬──────┴────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │  JSON Response with:   │
                    │  ├─ forecasts[]        │
                    │  ├─ policy_insights{}  │
                    │  └─ policy_charts[]    │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  Frontend Rendering    │
                    │  ├─ Forecast charts    │
                    │  ├─ Policy timeline    │
                    │  ├─ Contribution bars  │
                    │  ├─ Roadmap Gantt      │
                    │  ├─ Gap analysis       │
                    │  ├─ Recommendations    │
                    │  └─ Strategy actions   │
                    └────────────┬───────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  User Sees Complete    │
                    │  Analysis Dashboard    │
                    │  with Insights!        │
                    └────────────────────────┘
```

---

## Component Dependencies

```
Frontend Components:
└─ SmartUploadForecast
   ├─ ForecastVisualization
   │  ├─ Renders forecast charts
   │  └─ ForecastInsights (Q&A about forecasts)
   │     └─ Optional: Ask questions about results
   │
   └─ PolicyInsights (NEW!)
      ├─ Displays policy adoption timeline
      ├─ Shows contribution breakdown
      ├─ Lists policy gaps
      ├─ Shows recommendations
      └─ Displays forward strategy

Backend Components:
└─ Flask App (/api/upload-and-forecast)
   │
   ├─ File Processing
   │  └─ process_document()
   │
   ├─ Data Extraction
   │  └─ DataExtractor
   │
   ├─ Forecasting
   │  ├─ ForecastingService
   │  └─ AdvancedForecastingService
   │
   ├─ Policy Analysis (NEW!)
   │  └─ PolicyAnalyzer
   │     ├─ analyze_comprehensive_policy_impact()
   │     └─ LLM Integration (Ollama)
   │
   └─ Visualization (NEW!)
      └─ PolicyVisualizer
         ├─ create_policy_adoption_timeline()
         ├─ create_contribution_waterfall()
         ├─ create_strategic_roadmap()
         └─ create_policy_gap_analysis()
```

---

## Response Structure (JSON)

```json
{
  "status": "ok",
  "summary": {
    "files_processed": 1,
    "files_with_forecasts": 1,
    "total_models_trained": 4
  },
  "documents": [
    {
      "filename": "sales_data.xlsx",
      "status": "success",
      "extraction": { ... }
    }
  ],
  "forecasts": [
    {
      "filename": "sales_data.xlsx",
      "data_series": "Sales from Sheet1",
      "data_points": 24,
      "best_model": "XGBoost",
      "best_r2_score": 0.8934,
      "models_comparison": { ... }
    }
  ],
  
  // NEW: Policy Insights
  "policy_insights": {
    "policies_adopted_from_china": [
      {
        "policy_name": "EV Manufacturing Subsidies",
        "china_year": 2009,
        "india_year": 2015,
        "adaptation": "Modified for smaller segments",
        "forecast_impact": "8-10%",
        "success_level": "High"
      },
      ... (3 more policies)
    ],
    
    "policy_contribution_breakdown": {
      "manufacturing_incentives": {
        "percentage": 18,
        "description": "PLI scheme details",
        "impact": "Production capacity +400%"
      },
      ... (4 more categories)
    },
    
    "policy_gaps": [
      "Battery recycling framework",
      "Rural infrastructure",
      ... (6 more gaps)
    ],
    
    "strategic_recommendations": [
      {
        "title": "National Battery Recycling Policy",
        "priority": "Critical",
        "timeline": "2024-2025",
        "impact": "5-7% cost reduction",
        "rationale": "End-of-life battery management critical",
        "china_reference": "China's EPR for NEV Batteries (2018)"
      },
      ... (4 more recommendations)
    ],
    
    "forward_strategy": {
      "short_term_2024_2025": [
        "Launch national battery recycling policy",
        ... (4 more actions)
      ],
      "medium_term_2026_2028": [
        "Deploy 100K public charging stations",
        ... (4 more actions)
      ],
      "long_term_2029_2030": [
        "Achieve 30% EV penetration",
        ... (4 more actions)
      ]
    }
  },
  
  // NEW: Charts
  "policy_charts": [
    {
      "type": "timeline",
      "title": "Policy Adoption Timeline",
      "description": "Shows when India adopted policies from China",
      "image": "data:image/png;base64,iVBORw0KGgo..."
    },
    {
      "type": "waterfall",
      "title": "Policy Contribution Breakdown",
      "description": "% contribution of each policy category",
      "image": "data:image/png;base64,..."
    },
    {
      "type": "roadmap",
      "title": "Strategic Implementation Roadmap",
      "description": "Timeline for new policy initiatives",
      "image": "data:image/png;base64,..."
    },
    {
      "type": "gap_analysis",
      "title": "Policy Gap Analysis",
      "description": "Gaps vs adopted policies",
      "image": "data:image/png;base64,..."
    }
  ]
}
```

---

## Technology Stack

```
Frontend:
├─ Next.js / React
├─ Axios (HTTP client)
├─ Tailwind CSS (styling)
└─ JavaScript (ES6+)

Backend:
├─ Flask (web framework)
├─ Python 3.9+
├─ Flask-CORS (cross-origin requests)
├─ Pandas (data processing)
├─ NumPy (calculations)
├─ Scikit-learn (ML)
├─ XGBoost (gradient boosting)
├─ Prophet (time series)
├─ Statsmodels (ARIMA)
├─ Matplotlib (base plotting)
├─ Seaborn (enhanced plots)
├─ Langchain (LLM integration)
├─ Ollama (local LLM)
└─ PyPDF2/openpyxl (file parsing)

External:
├─ Ollama (Local LLM)
│  └─ Model: DeepSeek R1:14b
├─ MongoDB (optional, document storage)
└─ Standard HTTP/REST
```

---

## Deployment Architecture

```
Development:
├─ Frontend: npm run dev (port 3000)
└─ Backend: python run.py (port 5000)

Production (Docker):
├─ Frontend container (Next.js)
├─ Backend container (Flask + Python)
├─ Ollama container (LLM service)
└─ MongoDB container (optional)

docker-compose.yml:
├─ frontend service
├─ backend service
├─ ollama service
└─ mongodb service (optional)
```

---

**Architecture Last Updated:** February 2026  
**Status:** ✅ Production Ready & Tested
