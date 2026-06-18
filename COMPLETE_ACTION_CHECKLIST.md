# 📋 GENIVRA PROJECT - COMPLETE ACTION CHECKLIST

## PART 1: CRITICAL BLOCKERS (FIX FIRST - BLOCKING USERS)

### 🔴 BLOCKER #1: Frontend-Backend Connection Failing
- [ ] Verify API is running (`curl http://localhost:8000/health`)
- [ ] Verify frontend server is running (`curl http://localhost:8001`)
- [ ] Open browser dev tools (F12) on dashboard.html
- [ ] Check Network tab for `/predict` requests - look for CORS errors
- [ ] Check Console tab for JavaScript errors
- [ ] If CORS error: Verify `allow_origins=["*"]` in `API/main.py`
- [ ] If connection refused: Check if API port 8000 is already in use
- [ ] Test direct API call from browser console:
  ```javascript
  fetch('http://localhost:8000/health')
    .then(r => r.json())
    .then(d => console.log(d))
  ```
- [ ] If still failing: Configure a dev proxy or change frontend base URL

**Why:** Users can't submit predictions if frontend can't reach backend

---

### 🔴 BLOCKER #2: Dashboard Has No Prediction Form
- [ ] Open `FrontEnd/dashboard.html`
- [ ] Look at HTML structure - there's a summary table but no form
- [ ] Add HTML form section above the table with fields for:
  - [ ] Phase (text input)
  - [ ] Indication (text input)
  - [ ] Trial sample size (number input)
  - [ ] Trial duration weeks (number input)
  - [ ] Endpoint type (select: objective/subjective)
  - [ ] Primary endpoint name (select: CDR-SB/ADAS-Cog/MMSE)
  - [ ] Age mean (number input)
  - [ ] MMSE baseline (number input)
  - [ ] CDR baseline (number input)
  - [ ] APOE e4 carrier (checkbox: yes/no)
  - [ ] P-tau217 high (checkbox: yes/no)
  - [ ] Amyloid PET positive (checkbox: yes/no)
  - [ ] Submit button
- [ ] Add JavaScript event listener to submit button
- [ ] In listener: Gather form values → POST to `http://localhost:8000/predict`
- [ ] Display response in table below form
- [ ] Add error message display if prediction fails

**Why:** Currently users can only view results, not create new predictions

---

### 🔴 BLOCKER #3: No Error Handling on Frontend
- [ ] Wrap all `fetch()` calls in try/catch blocks
- [ ] Add error message div to HTML: `<div id="errorMessage" style="color: red;"></div>`
- [ ] Show error when API unreachable
- [ ] Show error when prediction fails
- [ ] Clear errors on successful submission
- [ ] Add loading spinner/message while awaiting response:
  - [ ] Show "Loading..." text
  - [ ] Disable submit button during request
  - [ ] Hide results while loading
- [ ] Add timeout (e.g., 30 seconds) if API doesn't respond

**Why:** Users see blank pages or confusing errors instead of helpful messages

---

## PART 2: HIGH PRIORITY (NEED TO DO SOON)

### 🟠 HIGH #1: Unified Frontend Experience
- [ ] Create a main app shell (could be simple HTML header/nav)
- [ ] Add navigation header with links to:
  - [ ] Dashboard (single prediction)
  - [ ] Upload Tool (batch predictions)
  - [ ] About/Help page
- [ ] Consistent header/footer across all pages
- [ ] Consistent styling/colors across all pages
- [ ] Move marketing site (`index.html`) to separate folder `/marketing/` or rename to `landing.html`
- [ ] Update `README.md` to clarify which frontend to use for what

**Why:** Users confused by 3 separate files with no navigation

---

### 🟠 HIGH #2: API Connection Validation
- [ ] Add health check to each HTML page on page load
- [ ] Code: Check `http://localhost:8000/health`
- [ ] Show green "Connected" indicator if OK
- [ ] Show red "Disconnected" warning if fails
- [ ] Disable prediction form if not connected
- [ ] Add button "Check API Connection" for manual test

**Why:** Users need to know if backend is ready before trying to submit

---

### 🟠 HIGH #3: Improve Dashboard.html Functionality
- [ ] Add tabs or sections for:
  - [ ] New Prediction (form)
  - [ ] Results Viewer (table + charts)
  - [ ] Batch Upload (link to upload.html or embed)
- [ ] Make dashboard.html the default entry point
- [ ] Add "Clear All" button to reset form and results
- [ ] Add "Export Results" button to download table as CSV
- [ ] Store last 10 predictions in browser localStorage
- [ ] Display prediction history on dashboard

**Why:** Dashboard is the main user interface and needs complete workflow

---

### 🟠 HIGH #4: Fix upload.html to Work with Dashboard
- [ ] Test CSV upload functionality (it might already work)
- [ ] Verify `/predict` endpoint accepts CSV rows
- [ ] Add link from dashboard to upload tool
- [ ] Allow importing upload results back to dashboard
- [ ] Show progress while processing multiple rows

**Why:** Users need way to batch process trials

---

## PART 3: MEDIUM PRIORITY (NICE TO HAVE)

### 🟡 MEDIUM #1: Form Validation on Frontend
- [ ] Add client-side validation for all form fields
- [ ] Required fields: Check not empty
- [ ] Number fields: Check valid numbers
- [ ] Age: Check 50-120 range
- [ ] MMSE: Check 0-30 range
- [ ] Sample size: Check > 0
- [ ] Duration: Check > 0
- [ ] Show validation error messages inline
- [ ] Prevent form submission if validation fails

---

### 🟡 MEDIUM #2: Better Results Display
- [ ] Show confidence color-coding (HIGH=green, MEDIUM=yellow, LOW=red)
- [ ] Show probability as percentage AND as visual progress bar
- [ ] Display top 5 drivers with visualizations
- [ ] Show which biomarkers were missing
- [ ] Display confidence explanation
- [ ] Add "Why this prediction?" expandable section

---

### 🟡 MEDIUM #3: API Key Management UI
- [ ] Add "Settings" page with API key input
- [ ] Store API key in localStorage (with warning about security)
- [ ] Use stored API key for all requests (instead of hardcoded)
- [ ] Add option to clear stored key

---

### 🟡 MEDIUM #4: Sample Data & Examples
- [ ] Add "Load Sample Trial" button
- [ ] Pre-fill form with realistic example data
- [ ] Add 3-5 different example scenarios
- [ ] Include comment explaining each example

---

### 🟡 MEDIUM #5: Responsive Design
- [ ] Test dashboard on mobile (it probably doesn't work)
- [ ] Stack form and results vertically on mobile
- [ ] Make buttons touch-friendly (larger)
- [ ] Optimize charts for small screens
- [ ] Test on tablet (iPad, Android)

---

## PART 4: LOW PRIORITY (POLISH)

### 🔵 LOW #1: Documentation & Help
- [ ] Add help tooltip on each form field
- [ ] Create FAQ section
- [ ] Link to API documentation
- [ ] Link to biomarker reference guide
- [ ] Add video tutorial (optional - you don't have one now)

---

### 🔵 LOW #2: Advanced Features
- [ ] Add prediction comparison tool (compare 2 trials side-by-side)
- [ ] Add filters to results table
- [ ] Add sorting to results table
- [ ] Add search in results table
- [ ] Dark/light theme toggle

---

### 🔵 LOW #3: Performance
- [ ] Minimize JavaScript bundle
- [ ] Cache API responses
- [ ] Add request debouncing
- [ ] Lazy load charts if many results

---

## PART 5: TESTING & VERIFICATION

### ✅ Functionality Tests
- [ ] Fill form → Click "Predict" → Get results (no errors)
- [ ] Check that probability 0-1 range is valid
- [ ] Check that risk tier is HIGH/MEDIUM/LOW
- [ ] Check that top drivers are present and numbered 1-5
- [ ] Test with different biomarker combinations
- [ ] Test with missing biomarkers (should still work)
- [ ] Upload CSV with 5 rows → All 5 should predict successfully
- [ ] Upload CSV with 1 invalid row → Show error for that row
- [ ] Navigate between dashboard/upload/marketing → No broken links
- [ ] Close browser → Reopen → History should persist (if implemented)

---

### 🔧 Integration Tests
- [ ] Start API + Frontend + Test workflow
- [ ] Make prediction → Verify correct model output
- [ ] Make batch predictions → Verify all rows process
- [ ] Check API logs show prediction requests
- [ ] Verify response times < 5 seconds

---

### 🐛 Error Scenario Tests
- [ ] API not running → Show helpful error message
- [ ] Invalid API response → Handle gracefully
- [ ] Network timeout (API slow) → Show timeout message
- [ ] Invalid form data → Show validation error
- [ ] Missing required fields → Show "Required" error
- [ ] Out-of-range values → Show "Invalid range" error
- [ ] Browser console → No JavaScript errors

---

## PART 6: BACKEND IMPROVEMENTS (IF TIME)

### Backend Fixes
- [ ] [ ] Add request logging to capture all predictions
- [ ] [ ] Add response caching for same input
- [ ] [ ] Add prediction versioning
- [ ] [ ] Add model performance metrics endpoint
- [ ] [ ] Add batch prediction endpoint (optimize CSV processing)

---

## PART 7: DEPLOYMENT PREP

### Pre-Production Checklist
- [ ] [ ] All frontend forms validated
- [ ] [ ] All errors handled gracefully
- [ ] [ ] API key not hardcoded in frontend
- [ ] [ ] CORS properly configured (not `["*"]` for prod)
- [ ] [ ] SSL/HTTPS enabled (if hosting on internet)
- [ ] [ ] API rate limiting working
- [ ] [ ] Monitoring & error logging in place
- [ ] [ ] Database setup (if using predictions)
- [ ] [ ] Backup & recovery procedure documented

---

## 📊 PRIORITY MATRIX

| Priority | Category | Effort | Impact | Status |
|----------|----------|--------|--------|--------|
| 🔴 BLOCKER | Frontend Connection | 1 hour | CRITICAL | TODO |
| 🔴 BLOCKER | Prediction Form | 1.5 hours | CRITICAL | TODO |
| 🔴 BLOCKER | Error Handling | 1 hour | CRITICAL | TODO |
| 🟠 HIGH | Frontend Unification | 2 hours | HIGH | TODO |
| 🟠 HIGH | API Validation | 0.5 hours | HIGH | TODO |
| 🟠 HIGH | Dashboard Improvements | 2 hours | HIGH | TODO |
| 🟠 HIGH | Upload.html Integration | 1 hour | HIGH | TODO |
| 🟡 MEDIUM | Form Validation | 1 hour | MEDIUM | TODO |
| 🟡 MEDIUM | Better Results UI | 1.5 hours | MEDIUM | TODO |
| 🟡 MEDIUM | API Key UI | 0.5 hours | MEDIUM | TODO |
| 🔵 LOW | Documentation | 1 hour | LOW | TODO |
| 🔵 LOW | Advanced Features | 3 hours | LOW | TODO |

---

## ⏱️ ESTIMATED TIMELINE

### Day 1 (Today): Fix Blockers
- 🔴 BLOCKER #1: Frontend Connection - 1 hour
- 🔴 BLOCKER #2: Add Prediction Form - 1.5 hours  
- 🔴 BLOCKER #3: Error Handling - 1 hour
- **Total: 3.5 hours** → Working MVP ✅

### Day 2: High Priority
- 🟠 Frontend Unification - 2 hours
- 🟠 API Validation - 0.5 hours
- 🟠 Dashboard Improvements - 2 hours
- 🟠 Upload.html Integration - 1 hour
- **Total: 5.5 hours** → Polished interface ✅

### Day 3: Medium Priority + Testing
- 🟡 Form Validation - 1 hour
- 🟡 Better Results UI - 1.5 hours
- 🟡 API Key UI - 0.5 hours
- ✅ Functionality Testing - 1.5 hours
- 🐛 Bug Fixes - 1 hour
- **Total: 5.5 hours** → Production ready ✅

---

## 🎯 SUCCESS CRITERIA

When complete, the project should:

✅ **User can make a prediction** by filling form on dashboard  
✅ **Results display correctly** with probability, risk tier, top drivers  
✅ **Error messages are helpful** when something fails  
✅ **Frontend shows API connection status** clearly  
✅ **User can upload CSV** and batch process predictions  
✅ **Navigation works** between dashboard, upload, and help pages  
✅ **No JavaScript errors** in browser console  
✅ **Responsive design** works on mobile/tablet  
✅ **All tests pass** (functionality + integration)  
✅ **Documentation is clear** for new users  

---

## 📝 NOTES

- Keep changes organized in version control (already on `andrew_dev2` branch)
- Test after each blocker is fixed
- Don't move to next section until current section is working
- If you get stuck on something, focus on another section and come back
- The 3 frontends are functional but disconnected - your goal is to make them work together

---

**Last Updated:** May 28, 2026  
**Complexity Level:** Medium (JavaScript frontend + API integration)  
**Estimated Total Time to Complete:** 14-16 hours
