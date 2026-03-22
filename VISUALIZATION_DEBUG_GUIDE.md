# Visualization Issue - Diagnosis & Solution

## Problem
Charts are not showing in the frontend.

## Root Cause Analysis

### Issue 1: Backend Timeout ❌
The backend is timing out when processing queries because:
- Ollama LLM (deepseek-r1:14b) is taking too long to respond
- No timeout configured on LLM calls
- Queries waiting indefinitely

### Issue 2: Missing Error Handling
- Frontend doesn't show loading state during LLM processing
- No timeout on API calls
- Users don't know if system is working or stuck

## Solutions Implemented

### ✅ Solution 1: Add LLM Timeout
```python
llm = OllamaLLM(
    model='deepseek-r1:14b',
    base_url='http://localhost:11434',
    timeout=60  # 60 second timeout
)
```

### ✅ Solution 2: Debug Logging
Added console logging to track:
- Backend: Query processing steps, chart generation
- Frontend: API responses, chart data received

### ✅ Solution 3: Better User Feedback
- Loading indicator shows "Analyzing..."
- Console logs help debug issues

## How to Test

### Step 1: Start Backend
```bash
cd backend
python run.py
```

### Step 2: Start Frontend  
```bash
cd frontend
npm run dev
```

### Step 3: Test Query
1. Go to http://localhost:3000
2. Enable "Enable chart visualization"
3. Ask: "What will be the EV market growth by 2030?"
4. Wait for response (may take 30-60 seconds for LLM)
5. Check browser console (F12) for debug logs

### Step 4: Check Logs

**Backend Terminal:**
```
[DEBUG] Query: What will be the EV market growth...
[DEBUG] Response keys: dict_keys(['text', 'sources', 'confidence', 'charts', 'has_visualization'])
[DEBUG] Has visualization: True
[DEBUG] Number of charts: 2
[DEBUG] Chart 0: line - Market Growth Forecast
[DEBUG] Chart 1: bar - Key Performance Indicators
```

**Frontend Console (F12):**
```javascript
Backend response: {response: "...", charts: [...], sources: [...]}
Charts received: [{type: "line", ...}, {type: "bar", ...}]
Number of charts: 2
Setting charts state: [{...}, {...}]
```

## Common Issues & Fixes

### Issue: "Backend is not responding"
**Fix:** Restart backend
```bash
cd backend
python run.py
```

### Issue: "Charts taking too long"
**Cause:** LLM model (deepseek-r1:14b) is large and slow
**Fix:** Use a smaller model
```bash
# In .env file or environment
export LLM_MODEL=llama2:7b  # Faster, smaller model
```

### Issue: "No charts shown"
**Debug Steps:**
1. Open browser console (F12)
2. Check for "Charts received" log
3. If charts=[], check backend logs
4. Verify "Enable chart visualization" is checked

### Issue: "Ollama not responding"
**Fix:**
```bash
# Restart Ollama
ollama serve

# Or restart the model
ollama run deepseek-r1:14b
```

## Performance Tips

### Use Faster Models
```bash
# Current (slow): deepseek-r1:14b (14 billion parameters)
ollama pull llama2:7b  # Much faster

# Update .env:
LLM_MODEL=llama2:7b
```

### Reduce Context Size
In `rag_agent.py`:
```python
# Change top_k from 5 to 3
docs = search_similar_documents(query_embedding, top_k=3)
```

### Add Caching
Cache common queries to avoid re-processing.

## Verification Checklist

Before asking a query:
- [ ] Backend running (http://localhost:4000)
- [ ] Frontend running (http://localhost:3000)
- [ ] Ollama running (`ollama serve`)
- [ ] "Enable chart visualization" is checked
- [ ] Browser console open (F12) to see logs

## Expected Behavior

### Forecast Query
**Input:** "What will be EV growth by 2030?"
**Output:**
- ✅ Text response with sources
- ✅ Confidence level badge
- ✅ 2-3 source documents listed
- ✅ Line chart (growth trend)
- ✅ Bar chart (key metrics)

### Comparison Query  
**Input:** "Compare growth with/without infrastructure"
**Output:**
- ✅ Text response with sources
- ✅ Bar chart (comparison)
- ✅ Line chart (trend)

### Distribution Query
**Input:** "Market share of OEMs"
**Output:**
- ✅ Text response
- ✅ Pie chart (distribution)

## Still Not Working?

### Quick Diagnostic
Run this test:
```bash
python test_chart_generation.py
```

Look for:
- Connection errors → Backend not running
- Timeout errors → LLM too slow, use smaller model
- No charts generated → Check keyword detection

### Get Debug Info
```bash
# Backend logs
cd backend
python run.py > backend.log 2>&1

# Check logs
cat backend.log | grep "\[DEBUG\]"
```

## Summary

✅ Timeout added to LLM (60 seconds)  
✅ Debug logging enabled  
✅ Frontend console logging added  
✅ Chart generation logic verified  

**Main Issue:** LLM response time is slow (30-60 seconds for deepseek-r1:14b)  
**Quick Fix:** Wait longer OR use smaller model (llama2:7b)  
**Long-term:** Add caching, reduce context, optimize prompts
