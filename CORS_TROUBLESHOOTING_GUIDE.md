# Agentic RAG Document Assistant - CORS & Network Error Troubleshooting

## Quick Start

### Option 1: Automated Startup (Recommended for Windows)
```bash
# Double-click one of these batch files from the project root:
START_APP.bat          # Starts both backend and frontend
START_BACKEND.bat      # Start only backend server
START_FRONTEND.bat     # Start only frontend server
```

### Option 2: Manual Startup
```bash
# Terminal 1: Backend (from project root)
cd backend
python run.py

# Terminal 2: Frontend (from project root)
cd frontend
npm run dev
```

**Default URLs:**
- Frontend: http://localhost:3000
- Backend: http://localhost:4000
- API Upload: http://localhost:4000/api/upload
- Health Check: http://localhost:4000/api/health

---

## ❌ CORS Error: "Cannot reach http://localhost:4000/api/upload"

### Root Causes & Solutions

#### 1. **Backend Not Running** (Most Common)
**Problem:** Backend server is not started
```
Error: Network/CORS error: cannot reach http://localhost:4000/api/upload
```

**Solution:**
```bash
# Open NEW terminal window and run:
cd backend
python run.py

# You should see:
# INFO:__main__:Starting server on port 4000 using wsgiref
# INFO:__main__:Server is listening on http://localhost:4000
```

**Verify backend is running:**
- Open browser: http://localhost:4000/api/health
- Should show: `{"status": "ok", "message": "Backend server is running"}`

---

#### 2. **Port 4000 Already in Use**
**Problem:** Another application is using port 4000
```
Error: OSError: [Errno 48] Address already in use
     or
Error: [WinError 10048] Only one usage of each socket address (protocol/IP address/port)
```

**Solution - Windows:**
```bash
# Find process using port 4000:
netstat -ano | findstr :4000

# Kill the process (replace PID with actual process ID):
taskkill /PID <PID> /F

# Or use a different port:
set PORT=5000
python run.py
```

**Solution - Mac/Linux:**
```bash
# Find process:
lsof -i :4000

# Kill the process:
kill -9 <PID>
```

---

#### 3. **CORS Not Configured Correctly**
**Problem:** Backend is running but frontend can't access it
```
Error in browser console:
Access to XMLHttpRequest at 'http://localhost:4000/api/upload' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution - Verify CORS is enabled in backend:**

Check file: `backend/app/__init__.py`
```python
# Should have this configuration:
CORS(app,
     resources={r"/api/*": {
         "origins": [
             "http://localhost:3000",
             "http://127.0.0.1:3000",
         ],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         ...
     }},
     automatic_options=True
)
```

**If CORS config is missing:**
1. Update the file with correct CORS configuration
2. Restart backend: `python run.py`

---

#### 4. **Frontend Using Wrong API URL**
**Problem:** Frontend is trying to reach wrong backend URL
```
Error: Cannot reach http://localhost:5000/api/upload
        (or http://example.com instead of localhost:4000)
```

**Solution - Check frontend configuration:**

**For Frontend .env.local:**
```bash
# Create or edit: frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:4000
```

**Verify in components:**
```javascript
// File: frontend/components/SmartUploadForecast.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:4000';

// Should show http://localhost:4000 in console:
console.log('API Base URL:', API_BASE_URL);
```

---

#### 5. **MongoDB Connection Issue**
**Problem:** Backend runs but database connection fails
```
Error: connection refused to MongoDB
```

**Solution:**
1. Check `.env` file has correct MONGO_URI:
```bash
cat backend/.env | grep MONGO_URI
```

2. Verify MongoDB is accessible:
```bash
# If using MongoDB Atlas (cloud):
# Ensure IP whitelist includes your machine

# If using local MongoDB:
mongod --version  # Verify MongoDB is installed
```

3. Update MONGO_URI if needed:
```
# Format: mongodb+srv://username:password@cluster.mongodb.net
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net
```

---

## 🔍 Diagnostic Tools

### Check Backend Health
```bash
# In browser or terminal:
curl http://localhost:4000/api/health

# Expected response:
# {"status": "ok", "service": "agentic-rag-backend", "port": 4000}
```

### Check Network Connectivity
```bash
# Verify localhost:4000 is accessible:
ping localhost:4000          # May not work for ports
curl -v http://localhost:4000/api/health

# On Windows:
netstat -an | findstr LISTENING
```

### Browser Console Debugging
```javascript
// Open DevTools (F12) > Console > paste this:

// Test 1: Can you reach backend?
fetch('http://localhost:4000/api/health')
  .then(r => r.json())
  .then(d => console.log('✓ Backend OK:', d))
  .catch(e => console.log('✗ Backend Error:', e.message));

// Test 2: CORS preflight
fetch('http://localhost:4000/api/upload', { method: 'OPTIONS' })
  .then(r => {
    console.log('✓ CORS Preflight OK');
    console.log('Headers:', r.headers.get('Access-Control-Allow-Origin'));
  })
  .catch(e => console.log('✗ CORS Error:', e.message));
```

---

## 🐛 Common Error Messages & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Network Error` | Backend not running | Run `python run.py` |
| `404 Not Found` | Wrong endpoint | Use `/api/upload` not `/upload` |
| `403 Forbidden` | CORS blocked | Check CORS config in app/__init__.py |
| `ECONNREFUSED` | Port not open | Check port 4000 is not in use |
| `CORS error: Access denied` | Origin not allowed | Add localhost:3000 to CORS origins |
| `Timeout` | Backend too slow | Try smaller files or fewer requests |
| `413 Payload Too Large` | File size exceeds limit | Check MAX_CONTENT_LENGTH in config |

---

## ✅ Verification Checklist

Use this checklist to verify everything is configured correctly:

```
BACKEND SETUP:
☐ Backend folder exists at: backend/
☐ requirements.txt exists with Flask-CORS
☐ .env file exists in backend/
☐ MongoDB URI is set correctly in .env

BACKEND RUNNING:
☐ Terminal shows "Server is listening on http://localhost:4000"
☐ No port already in use errors
☐ http://localhost:4000/api/health returns OK in browser

CORS CONFIGURATION:
☐ app/__init__.py has CORS(app, ...) config
☐ Origins include "http://localhost:3000"
☐ Methods include ["GET", "POST", "OPTIONS"]
☐ Headers include ["Content-Type", "Authorization"]

FRONTEND SETUP:
☐ frontend/ folder exists
☐ npm packages installed (node_modules/ exists)
☐ .env.local has NEXT_PUBLIC_API_BASE_URL=http://localhost:4000
☐ Frontend runs with: npm run dev

FRONTEND RUNNING:
☐ Terminal shows "ready - started server on 0.0.0.0:3000"
☐ Browser can reach http://localhost:3000
☐ No JavaScript errors in browser console

API ENDPOINT:
☐ Endpoint: http://localhost:4000/api/upload
☐ Method: POST
☐ Content-Type: No manual header (FormData sets it)
☐ Body: FormData with "files" field
```

---

## 📮 Test Upload Using curl (Command Line)

If browser upload fails, test with curl:

```bash
# Create test file
echo "Test content" > test.txt

# Windows PowerShell:
$headers = @{
    'Origin' = 'http://localhost:3000'
}
Invoke-WebRequest -Uri "http://localhost:4000/api/upload" `
  -Method POST `
  -Form @{'files'=@([IO.FileInfo] (Get-Item 'test.txt'))} `
  -Headers $headers

# Linux/Mac:
curl -X POST \
  -H "Origin: http://localhost:3000" \
  -F "files=@test.txt" \
  http://localhost:4000/api/upload
```

---

## 🔧 Advanced Configuration

### Change Backend Port
```bash
# Option 1: Command line
set PORT=5000
python run.py

# Option 2: .env file
PORT=5000
```

### Change Frontend Port
```bash
# Edit: frontend/package.json or:
npm run dev -- -p 3001
```

### Use Different MongoDB Database
```bash
# Edit backend/.env
MONGO_URI=mongodb+srv://newuser:newpass@newcluster.mongodb.net
```

---

## 🚀 Production Deployment

For production, use Docker:
```bash
# From project root:
docker-compose up --build

# Frontend: http://localhost:3000
# Backend: http://localhost:4000
```

---

## 💡 Need More Help?

**Check these logs:**
```bash
# Backend logs:
cat backend/logs/backend_*.log

# Check specific errors:
tail -f backend/logs/backend_*.log

# Frontend errors:
# Open http://localhost:3000
# Press F12 > Console tab
```

**Verify installation:**
```bash
python --version    # Should be 3.8+
pip list | grep Flask
npm --version       # Should be 14+
node --version
```

---

## Configuration Files Reference

**backend/.env**
```
SECRET_KEY=your_secret_key
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=deepseek-r1:14b
EMBEDDING_MODEL=nomic-embed-text
PORT=4000
HOST=0.0.0.0
```

**frontend/.env.local**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:4000
```

**backend/app/__init__.py** (CORS section)
```python
CORS(app,
     resources={r"/api/*": {
         "origins": [
             "http://localhost:3000",
             "http://127.0.0.1:3000",
         ],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True,
     }})
```

---

## Quick Commands Reference

```bash
# Backend startup
cd backend && python run.py

# Frontend startup
cd frontend && npm run dev

# Check what's using port 4000 (Windows)
netstat -ano | findstr :4000

# Kill process on port 4000 (Windows)
taskkill /PID <PID> /F

# Check MongoDB connection (if installed)
mongosh "mongodb+srv://user:pass@cluster.mongodb.net/test"

# View backend logs (Windows PowerShell)
Get-Content backend/logs/backend_*.log -Tail 20

# View frontend logs
npm run dev 2>&1 | Tee-Object frontend_logs.txt
```

---

**Last Updated:** 2026-03-21  
**For Issues:** Check browser console (F12), backend logs, and this guide
