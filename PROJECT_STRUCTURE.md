# Project Structure Overview

## Directory Layout

```
FinalYRproject/
├── 📄 README.md                          # Project overview
├── 📄 ARCHITECTURE.md                    # Complete system architecture
├── 📄 SETUP_GUIDE.md                     # Quick start guide
├── 📄 IMPLEMENTATION_SUMMARY.md          # What was implemented (THIS FILE)
├── 📄 docker-compose.yml                 # Docker configuration
│
├── 📁 backend/                           # Flask Backend (Port 5000)
│   ├── 🐍 run.py                         # Entry point
│   ├── 🐍 config.py                      # Configuration settings
│   ├── 📄 requirements.txt                # Python dependencies
│   ├── 📄 Dockerfile                     # Docker image
│   │
│   ├── 📁 app/                           # Main application package
│   │   ├── 🐍 __init__.py                # App factory & blueprint registration
│   │   ├── 🐍 database.py                # MongoDB connection
│   │   │
│   │   ├── 📁 agents/                    # Analysis agents
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 rag_agent.py           # RAG engine (LangChain + Ollama)
│   │   │   ├── 🐍 market_forecaster.py   # ✨ NEW: Forecasting module
│   │   │   │   ├── Prophet forecasting
│   │   │   │   ├── ARIMA models
│   │   │   │   ├── XGBoost predictions
│   │   │   │   ├── Ensemble forecasting
│   │   │   │   └── OEM market share tracking
│   │   │   └── 🐍 policy_analyzer.py     # ✨ NEW: Policy analysis module
│   │   │       ├── Policy extraction
│   │   │       ├── Policy comparison
│   │   │       ├── Impact assessment
│   │   │       └── Recommendations
│   │   │
│   │   ├── 📁 models/                    # Data models
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 document.py            # MongoDB document schema
│   │   │
│   │   ├── 📁 routes/                    # API endpoints
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 upload.py              # Document upload (PDF/Excel)
│   │   │   ├── 🐍 query.py               # RAG query endpoint
│   │   │   └── 🐍 analysis.py            # ✨ NEW: Analysis endpoints
│   │   │       ├── POST /api/forecast/market
│   │   │       ├── POST /api/forecast/ev-adoption
│   │   │       ├── POST /api/forecast/oem-market-share
│   │   │       ├── POST /api/policy/extract
│   │   │       ├── POST /api/policy/compare
│   │   │       ├── POST /api/policy/recommendations
│   │   │       ├── POST /api/oem/strategy
│   │   │       └── GET /api/insights/market
│   │   │
│   │   ├── 📁 utils/                     # Utility modules
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 document_processor.py  # PDF/Excel text extraction
│   │   │   ├── 🐍 embeddings.py          # Vector embeddings
│   │   │   └── 🐍 vector_search.py       # MongoDB vector search
│   │   │
│   │   └── 📁 __pycache__/
│   │
│   ├── 📁 uploads/                       # Uploaded documents storage
│   └── 📁 __pycache__/
│
├── 📁 frontend/                          # Next.js Frontend (Port 3000)
│   ├── 📄 package.json                   # NPM dependencies
│   ├── 📄 tailwind.config.js             # Tailwind CSS config
│   ├── 📄 postcss.config.js              # PostCSS config
│   ├── 📄 Dockerfile                     # Docker image
│   │
│   ├── 📁 pages/                         # Next.js pages
│   │   ├── 🔵 _app.js                    # App wrapper
│   │   └── 🔵 index.js                   # Main dashboard
│   │
│   ├── 📁 components/                    # React components
│   │   ├── 🔵 FileUpload.js              # Document upload component
│   │   └── 🔵 QueryForm.js               # Query interface component
│   │
│   ├── 📁 styles/                        # CSS styles
│   │   └── 📄 globals.css                # Global styles
│   │
│   ├── 📁 public/                        # Static files
│   └── 📁 node_modules/                  # Node dependencies (generated)
│
└── 📁 data/                              # ✨ RECOMMENDED: Data directory
    ├── 📁 raw/
    │   ├── 📁 china/
    │   │   ├── 📁 policies/              # China policy PDFs
    │   │   ├── 📁 market_data/           # China market Excel
    │   │   └── 📁 oem_performance/       # China OEM data
    │   └── 📁 india/
    │       ├── 📁 regulations/           # India regulation PDFs
    │       └── 📁 market_data/           # India market Excel
    ├── 📁 processed/
    │   ├── extracted_policies.json
    │   ├── market_metrics.csv
    │   └── forecast_data.parquet
    └── 📁 insights/
        ├── policy_mappings.json
        └── predictions.json
```

---

## Key Files & Responsibilities

### Core Backend Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `run.py` | Entry point | Starts Flask server |
| `config.py` | Configuration | MongoDB URI, API keys, settings |
| `app/__init__.py` | App factory | Creates and registers blueprints |
| `app/database.py` | DB connection | MongoDB initialization |

### RAG & Analysis Agents

| File | Purpose | Key Functions |
|------|---------|---------------|
| `agents/rag_agent.py` | RAG engine | Document retrieval & analysis |
| `agents/market_forecaster.py` | Forecasting | Time series predictions |
| `agents/policy_analyzer.py` | Policy analysis | Extract & compare policies |

### API Routes

| File | Endpoints | Purpose |
|------|-----------|---------|
| `routes/upload.py` | POST /api/upload | Upload documents |
| `routes/query.py` | POST /api/query | RAG queries |
| `routes/analysis.py` | POST /api/forecast/* | Forecasting |
| | POST /api/policy/* | Policy analysis |
| | GET /api/insights/* | Market insights |

### Utilities

| File | Purpose | Key Functions |
|------|---------|---------------|
| `utils/document_processor.py` | Document parsing | Extract from PDF/Excel |
| `utils/embeddings.py` | Vector embeddings | Generate embeddings |
| `utils/vector_search.py` | Vector search | MongoDB search |

### Frontend

| File | Purpose | Content |
|------|---------|---------|
| `pages/index.js` | Main dashboard | Dashboard layout |
| `components/FileUpload.js` | File upload | Upload interface |
| `components/QueryForm.js` | Query interface | Query input form |

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  USER INTERFACE                          │
│              (Next.js Frontend - Port 3000)              │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ├─ File Upload (PDF/Excel)                       │   │
│  │ ├─ Query Input (Market questions)                │   │
│  │ └─ Results Display (Forecasts, insights)         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────────────────────┐
│              FLASK BACKEND - Port 5000                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ API Routes Layer                                 │   │
│  │ ├─ POST /api/upload          → upload_bp        │   │
│  │ ├─ POST /api/query           → query_bp         │   │
│  │ └─ POST /api/forecast/*      → analysis_bp      │   │
│  │ ├─ POST /api/policy/*        → analysis_bp      │   │
│  │ └─ GET /api/insights/*       → analysis_bp      │   │
│  └──────────────────────────────────────────────────┘   │
│                     │                                     │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │ Processing & Analysis Layer                     │   │
│  │ ├─ document_processor.py (PDF/Excel extract)   │   │
│  │ ├─ embeddings.py (Vector generation)           │   │
│  │ ├─ rag_agent.py (LangChain + Ollama)           │   │
│  │ ├─ market_forecaster.py (ML models)            │   │
│  │ └─ policy_analyzer.py (Policy extraction)      │   │
│  └──────────────────────────────────────────────────┘   │
│                     │                                     │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │ Data Layer                                       │   │
│  │ └─ MongoDB (Documents, embeddings, forecasts)   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
                          │
                ┌─────────▼────────┐
                │    Ollama LLM    │
                │  (Local, Offline) │
                │ DeepSeek-R1:14b  │
                └──────────────────┘
```

---

## Processing Pipeline

```
Step 1: DOCUMENT UPLOAD
  Input: PDF or Excel files
  Process: document_processor.py
  Output: Extracted text + embeddings
  Storage: MongoDB

Step 2: VECTOR INDEXING
  Input: Extracted text
  Process: embeddings.py
  Output: Vector embeddings
  Storage: MongoDB with vector search index

Step 3: USER QUERY/ANALYSIS REQUEST
  Input: Question or analysis request
  Process: Routes receive request
  Routing:
    - Query → rag_agent.py
    - Forecast → market_forecaster.py
    - Policy → policy_analyzer.py

Step 4: RAG PROCESSING
  Input: User query
  Process: rag_agent.py
    ├─ Generate query embedding
    ├─ Vector search in MongoDB
    ├─ Retrieve top-5 similar documents
    ├─ Create context from documents
    └─ Call Ollama LLM with context

Step 5: ANALYSIS PROCESSING
  Input: Documents or data
  Market Forecasting:
    ├─ Prepare time series data
    ├─ Prophet model training
    ├─ ARIMA model training
    ├─ XGBoost model training
    ├─ Ensemble prediction
    └─ Confidence scoring

  Policy Analysis:
    ├─ Extract policy keywords
    ├─ Map to policy domains
    ├─ Compare with other policies
    ├─ Calculate alignment score
    └─ Generate recommendations

Step 6: RESPONSE
  Output: JSON formatted result
  Return: To frontend
  Display: User sees insights/forecasts
```

---

## Technology Stack Summary

### Backend
```
Language: Python 3.x
Framework: Flask 2.3.3
API: RESTful JSON
Database: MongoDB 5.0+
LLM Framework: LangChain
LLM Engine: Ollama (DeepSeek-R1:14b)
ML Models: Prophet, ARIMA, XGBoost
NLP: spaCy, Transformers, scikit-learn
Data Processing: Pandas, NumPy
Testing: pytest (ready)
```

### Frontend
```
Framework: Next.js 13+
Runtime: Node.js 16+
Styling: Tailwind CSS
Components: React 18+
HTTP Client: Axios
```

### Infrastructure
```
Containerization: Docker
Orchestration: Docker Compose
Deployment: Production-ready
```

---

## Execution Flow

```
User Action                    Backend Processing         Database/LLM
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  1. Upload File               → document_processor.py → MongoDB   │
│     (PDF/Excel)                 ├─ Extract text                  │
│                                 ├─ Generate embeddings           │
│                                 └─ Store document                │
│                                                                   │
│  2. Query Question            → rag_agent.py                      │
│     (Text input)                 ├─ Create query embedding        │
│                                  ├─ Vector search (MongoDB)       │
│                                  ├─ Retrieve top-5 docs           │
│                                  ├─ Format context                │
│                                  └─ Call Ollama LLM → Response    │
│                                                                   │
│  3. Request Forecast          → market_forecaster.py             │
│     (Historical data)            ├─ Parse data                   │
│                                  ├─ Prophet model                │
│                                  ├─ ARIMA model                  │
│                                  ├─ XGBoost model                │
│                                  └─ Ensemble → Response          │
│                                                                   │
│  4. Policy Analysis           → policy_analyzer.py               │
│     (Comparison request)         ├─ Extract policies             │
│                                  ├─ Map to domains               │
│                                  ├─ Calculate alignment          │
│                                  └─ Generate recommendations     │
│                                                                   │
│  5. Get Insights              → analysis_bp routes               │
│     (Market metrics)             ├─ Compile metrics              │
│                                  ├─ Identify trends              │
│                                  └─ Format insights              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
         Display Results on Frontend Dashboard
```

---

## Important Notes

### ✅ What's Ready
- Backend API fully functional
- All agents implemented
- Routes registered
- Documentation complete

### ⏳ What You Need to Do
1. Organize your data in the `data/` folder structure
2. Start Ollama (if using local LLM)
3. Start MongoDB
4. Run backend: `python run.py`
5. Run frontend: `npm run dev`
6. Test API endpoints

### 📦 Dependencies
- All Python packages in `requirements.txt`
- All Node packages in `frontend/package.json`
- Ollama must be running (local LLM)
- MongoDB must be running

---

**Your project structure is now complete and aligned with automotive market analysis theme!** 🚗📊
