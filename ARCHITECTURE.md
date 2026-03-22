# Automotive Market Analysis Platform
## China's Automotive Dominance: Strategic Analysis for Indian OEMs

### Project Overview

This is an **Agentic RAG (Retrieval-Augmented Generation) system** designed to analyze China's automotive market dominance and provide strategic insights for Indian OEMs (Original Equipment Manufacturers).

**Key Features:**
- Multi-document analysis (PDFs & Excel files)
- Policy extraction and comparison (China vs India)
- Time series forecasting (Prophet, ARIMA, XGBoost)
- OEM market share predictions
- Strategic recommendations for Indian automotive industry

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│         Document Upload & Query Interface                    │
└─────────────┬───────────────────────────────────┬────────────┘
              │                                   │
         Upload                              Query/Analysis
              │                                   │
┌─────────────▼───────────────────────────────────▼────────────┐
│                  Backend (Flask API)                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Agentic RAG Layer                        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ - Document Processing (PDF/Excel extraction)         │   │
│  │ - Vector Embeddings & Semantic Search                │   │
│  │ - RAG Agent (LangChain + Ollama)                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Analysis Agents Layer                        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 1. Policy Analyzer                                   │   │
│  │    - Extract policies from documents                 │   │
│  │    - Compare China vs India policies                 │   │
│  │    - Generate recommendations                        │   │
│  │                                                       │   │
│  │ 2. Market Forecaster                                 │   │
│  │    - Prophet time series forecasting                 │   │
│  │    - ARIMA models for market trends                  │   │
│  │    - XGBoost for EV adoption                         │   │
│  │    - Ensemble predictions                            │   │
│  │                                                       │   │
│  │ 3. NLP Processors                                    │   │
│  │    - Named Entity Recognition (NER)                  │   │
│  │    - Sentiment analysis                              │   │
│  │    - Policy impact assessment                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Data & Storage Layer                     │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ - MongoDB: Documents, embeddings, forecasts          │   │
│  │ - Vector Search: Similarity matching                 │   │
│  │ - Cache: Recent queries and predictions              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                           │
                           │ Database Connection
                           │
                    ┌──────▼──────┐
                    │  MongoDB    │
                    │ with Vector │
                    │   Search    │
                    └─────────────┘
```

---

## API Endpoints

### 1. Document Management
- **POST** `/api/upload` - Upload research documents (PDF/Excel)
- **GET** `/api/documents` - List uploaded documents

### 2. Query & Analysis
- **POST** `/api/query` - Query documents using RAG agent
  - Analyzes China's automotive market policies
  - Compares with India's current state
  - Returns strategic insights

### 3. Market Forecasting
- **POST** `/api/forecast/market` - Forecast India's automotive market metrics
  - Input: Historical market data
  - Output: 3-year forecasts (Prophet, ARIMA, XGBoost)

- **POST** `/api/forecast/ev-adoption` - Forecast EV adoption rates
  - Predicts India's EV penetration timeline
  - Compares with China's trajectory

- **POST** `/api/forecast/oem-market-share` - Forecast OEM market share evolution
  - Individual OEM predictions
  - Market consolidation trends

### 4. Policy Analysis
- **POST** `/api/policy/extract` - Extract policies from documents
  - Identifies policy keywords and domains
  - Categorizes by: EV Incentives, Manufacturing, Environmental, Trade, R&D

- **POST** `/api/policy/compare` - Compare China vs India policies
  - Alignment scores (0-100)
  - Policy gaps analysis
  - Mutual focus areas

- **POST** `/api/policy/recommendations` - Get policy recommendations
  - Priority domains for India
  - Implementation roadmap
  - Success factors

### 5. Strategic Insights
- **POST** `/api/oem/strategy` - OEM strategy recommendations
  - Short/medium/long-term strategies
  - Competitive advantages
  - Risk assessment

- **GET** `/api/insights/market` - Key market insights
  - Industry trends
  - Market metrics (China vs India)
  - Strategic focus areas

---

## Data Structure

### Document Upload
```json
{
  "files": ["china_market_report.pdf", "india_regulations.xlsx"]
}
```

### Market Forecasting Input
```json
{
  "data": [
    {"date": "2020-01-01", "sales": 1000, "ev_percentage": 2},
    {"date": "2020-02-01", "sales": 1050, "ev_percentage": 2.3}
  ],
  "forecast_periods": 36
}
```

### Policy Analysis Input
```json
{
  "documents": [
    {"filename": "china_policy.pdf", "content": "...extracted text..."},
    {"filename": "india_regulations.xlsx", "content": "...extracted text..."}
  ]
}
```

---

## Key Technologies

### Backend
- **Framework**: Flask 2.3.3
- **RAG System**: LangChain + Ollama
- **Database**: MongoDB with Vector Search
- **Forecasting**: Prophet, ARIMA, XGBoost
- **NLP**: spaCy, Transformers
- **Data Processing**: Pandas, NumPy, scikit-learn

### Frontend
- **Framework**: Next.js
- **Styling**: Tailwind CSS
- **Components**: React
- **API Client**: Axios

### LLM
- **Model**: Ollama (DeepSeek-R1:14b)
- **Local Deployment**: No cloud dependencies

---

## Installation & Setup

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Using Docker
```bash
docker-compose up --build
```

---

## Data Organization

```
data/
├── raw/
│   ├── china/
│   │   ├── policies/          # China regulatory documents (PDFs)
│   │   ├── market_data/       # Sales, production, metrics (Excel)
│   │   └── oem_performance/   # OEM-specific data (Excel)
│   └── india/
│       ├── regulations/       # India policy documents (PDFs)
│       └── market_data/       # Current market stats (Excel)
├── processed/
│   ├── extracted_policies.json
│   ├── market_metrics.csv
│   └── forecast_data.parquet
└── insights/
    ├── policy_mappings.json
    └── predictions.json
```

---

## Usage Example

### 1. Upload Market Research
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "files=@china_auto_policy.pdf" \
  -F "files=@india_market_2024.xlsx"
```

### 2. Query for Insights
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What EV policies has China implemented that India could adopt?"
  }'
```

### 3. Get Market Forecast
```bash
curl -X POST http://localhost:5000/api/forecast/market \
  -H "Content-Type: application/json" \
  -d '{
    "data": [...market_data...],
    "forecast_periods": 36
  }'
```

### 4. Compare Policies
```bash
curl -X POST http://localhost:5000/api/policy/compare \
  -H "Content-Type: application/json" \
  -d '{
    "china_policies": {...},
    "india_policies": {...}
  }'
```

---

## Analysis Capabilities

### 1. Policy Domains Analyzed
- **EV Incentives**: Subsidies, tax credits, purchase incentives
- **Manufacturing**: Local content, production quotas, tech transfer
- **Environmental**: Emissions standards, fuel efficiency, carbon pricing
- **Trade**: Tariffs, import duties, market access
- **R&D**: Innovation grants, research funding

### 2. Market Metrics Forecasted
- Total automotive market growth
- EV market penetration
- OEM market share dynamics
- Production capacity trends
- Consumer purchasing patterns

### 3. Strategic Outputs
- China-India policy alignment scores (0-100)
- Market scenario generation
- OEM competitiveness assessment
- Implementation roadmaps
- Risk and opportunity analysis

---

## Current Limitations & Future Enhancements

### Current
- ✅ Document processing (PDF/Excel)
- ✅ RAG-based analysis
- ✅ Policy extraction and comparison
- ✅ Multiple forecasting models
- ✅ OEM strategy recommendations

### Future
- [ ] Real-time data integration
- [ ] Supply chain analysis
- [ ] Competitor intelligence
- [ ] Regulatory change tracking
- [ ] Interactive dashboards
- [ ] Advanced scenario planning
- [ ] Automated report generation

---

## Project Team

**Final Year Project** - Strategic Automotive Analysis Platform

---

## License

This project is part of academic research and follows institutional guidelines.

---

## Contact & Support

For questions or issues, refer to the project documentation or contact the development team.
