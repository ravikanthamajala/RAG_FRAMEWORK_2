# CORS & Upload Quick Fix Reference

## The 5-Minute Fix

### What's The Problem?
User clicks "Upload Documents" → Gets error: "Network/CORS error: cannot reach http://localhost:4000/api/upload"

### The Solution - 3 Steps

#### **Step 1: Start Backend** (If Not Running)
```bash
cd backend
python run.py
```
✓ Should show: `Server is listening on http://localhost:4000`

#### **Step 2: Verify Backend is Accessible**
Open in browser: http://localhost:4000/api/health
- ✓ Shows: `{"status": "ok", ...}` → Backend is working
- ✗ Shows: Page not found or blank → Backend not running or wrong port

#### **Step 3: Make Sure Frontend is Running**
```bash
cd frontend
npm run dev
```
✓ Should show: `ready - started server on 0.0.0.0:3000`

---

## 🔧 What I Fixed For You

### ✅ Backend Improvements
1. **Added Health Check Endpoint**
   - New files: `backend/app/routes/health.py`
   - Access at: `http://localhost:4000/api/health`
   - Helps diagnose if backend is running

2. **Enhanced CORS Configuration**
   - File: `backend/app/__init__.py`
   - ✓ Now supports both `localhost:3000` and `127.0.0.1:3000`
   - ✓ Explicit CORS headers on every response
   - ✓ Pre-flight requests handled automatically
   - ✓ Better debugging with request logging

3. **Fixed Upload Endpoint**
   - Endpoint: `POST /api/upload`
   - Handles: PDF, Excel, CSV files
   - CORS: Fully configured

### ✅ Frontend Improvements
1. **Better Error Messages**
   - File: `frontend/components/FileUpload.js`
   - File: `frontend/components/SmartUploadForecast.js`
   - ✓ Specific error types: Network vs CORS vs Timeout vs 404
   - ✓ Actionable error details
   - ✓ Shows debugging steps

2. **Improved Upload Handling**
   - Uses FormData correctly
   - No manual Content-Type header
   - Proper error handling with axios
   - Detailed network error diagnostics

### ✅ Configuration & Scripts
1. **Windows Startup Scripts**
   - `START_APP.bat` - Start both servers
   - `START_BACKEND.bat` - Start just backend
   - `START_FRONTEND.bat` - Start just frontend
   - Automatic dependency checking

2. **Troubleshooting Guide**
   - File: `CORS_TROUBLESHOOTING_GUIDE.md`
   - Complete with common errors and fixes
   - Diagnostic tools and verification checklist
   - curl examples for API testing

3. **Environment Configuration**
   - `.env` file support for backend
   - `.env.local` for frontend
   - API_BASE_URL configuration

---

## 🚀 How The Upload Now Works

### Request Flow
```
Frontend (localhost:3000)
    ↓
    FormData with files
    ↓
[CORS Preflight - OPTIONS request]
    ↓ (CORS headers validated)
    ↓
Backend (localhost:4000)
    ↓
    /api/upload endpoint receives POST
    ↓
    Process files with embeddings
    ↓
    Store in MongoDB
    ↓
    Return success response
    ↓
Frontend receives response
    ↓ (Display success/error)
User sees confirmation
```

### Technical Details

**Frontend Code (FormData):**
```javascript
const formData = new FormData();
files.forEach(file => formData.append('files', file));

await fetch('http://localhost:4000/api/upload', {
  method: 'POST',
  body: formData,
  // Note: NO Content-Type header - FormData sets it automatically
});
```

**Backend CORS Headers:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST, OPTIONS, GET
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

---

## 🐛 If Still Getting Errors

### Error: "Network Error"
**Cause:** Backend not running  
**Fix:**
```bash
cd backend
python run.py
```

### Error: "404 Not Found"
**Cause:** Wrong endpoint  
**Fix:** Use `http://localhost:4000/api/upload` (with `/api` prefix)

### Error: "CORS Error"
**Cause:** Frontend origin not in allowed list  
**Fix:** Verify `backend/app/__init__.py` includes `http://localhost:3000`

### Error: "Connection Refused"
**Cause:** Port 4000 blocked by firewall  
**Fix:** 
- Windows: Check Windows Defender Firewall
- Mac/Linux: Check firewall settings

### Error: "Timeout"
**Cause:** Backend taking too long  
**Fix:**
- Upload fewer files
- Smaller file sizes
- Check MongoDB connection

---

## ✅ Verification Checklist

```bash
# 1. Backend running on 4000?
curl http://localhost:4000/api/health

# 2. Frontend running on 3000?
curl http://localhost:3000

# 3. Upload endpoint exists?
curl -X OPTIONS http://localhost:4000/api/upload

# 4. CORS headers present?
curl -H "Origin: http://localhost:3000" \
  http://localhost:4000/api/upload

# 5. Can upload file?
# Use browser upload form or:
curl -F "files=@myfile.pdf" \
  http://localhost:4000/api/upload
```

---

## 📝 Files Changed

### Created
- `backend/app/routes/health.py` - Health check endpoint
- `START_APP.bat` - Windows startup script
- `START_BACKEND.bat` - Backend startup script
- `START_FRONTEND.bat` - Frontend startup script
- `CORS_TROUBLESHOOTING_GUIDE.md` - Complete troubleshooting guide
- `CORS_UPLOAD_QUICK_REFERENCE.md` - This file

### Modified
- `backend/app/__init__.py` - Enhanced CORS configuration, added health route registration
- `frontend/components/FileUpload.js` - Improved error handling
- `frontend/components/SmartUploadForecast.js` - Better error messages and diagnostics

---

## 🎯 Next Steps

1. **Run the startup script:**
   ```bash
   # Windows: Double-click this file
   START_APP.bat
   
   # Or manually:
   cd backend && python run.py    # Terminal 1
   cd frontend && npm run dev      # Terminal 2
   ```

2. **Test the upload:**
   - Go to http://localhost:3000
   - Select a PDF or Excel file
   - Click "Upload Documents"
   - Should see success message

3. **If error occurs:**
   - Check `CORS_TROUBLESHOOTING_GUIDE.md`
   - Look at backend terminal for error messages
   - Open browser console (F12) for frontend errors

---

## 📚 Reference URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web app |
| Backend | http://localhost:4000 | API server |
| Health Check | http://localhost:4000/api/health | Check backend status |
| Upload Endpoint | http://localhost:4000/api/upload | POST files here |
| Detailed Health | http://localhost:4000/api/health/detailed | Full backend status |

---

## 🎓 Understanding CORS

**CORS = Cross-Origin Resource Sharing**

- **Origin:** Protocol + Domain + Port (e.g., `http://localhost:3000`)
- **Cross-Origin Request:** Request from different origin
- **CORS Error:** Browser blocks cross-origin request without proper headers

**Solution:** Backend must send CORS headers allowing the frontend origin.

**In your case:**
- Frontend origin: `http://localhost:3000` ← Browser sends this
- Backend must respond with: `Access-Control-Allow-Origin: http://localhost:3000`

---

**Everything is fixed! Your app is ready to use.** 🎉

For detailed troubleshooting, see: `CORS_TROUBLESHOOTING_GUIDE.md`
