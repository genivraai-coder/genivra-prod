# Genivra Dashboard - Quick Start

This folder contains the dashboard UI and the files needed to run the frontend locally.

## Open Dashboard

### Option 1: Direct File (Easiest)
```bash
# Windows
start FrontEnd/dashboard.html

# macOS/Linux
open FrontEnd/dashboard.html
```

### Option 2: Web Server
```bash
# Python 3
python -m http.server 8001 --directory FrontEnd
# Then visit: http://localhost:8001/dashboard.html
```

---

## Start API (Required)

```bash
uvicorn API.main:app --host 127.0.0.1 --port 8000 --reload
```

Dashboard will show "✓ Connected to API" when API is ready.

---

## What You Can Do

### Tab 1: Single Trial Prediction
- Fill in trial design, endpoints, biomarkers
- Click "Predict Trial Success"
- Get back: probability, risk tier, feature drivers, confidence

### Tab 2: Batch Predictions
- Upload CSV with multiple trials
- Download example CSV format
- Get results table with per-row predictions
- Export results as CSV

---

## Sample CSV (Auto-Download Available)

```csv
trial_sample_size,trial_duration_weeks,phase,indication,trial_design,endpoint_type,primary_endpoint_name,age_mean
200,52,Phase 3,Alzheimer's disease,Double Blind,objective,CDR-SB,72.5
180,26,Phase 2,Mild Cognitive Impairment,RCT,subjective,ADAS-Cog,70.0
300,52,Phase 3,Alzheimer's disease,Double Blind,mixed,ADCOMS,74.2
```

---

## Features

✅ Real-time single trial prediction  
✅ Batch CSV upload & processing  
✅ 5 top feature drivers per prediction  
✅ Biomarker impact explanation  
✅ Confidence assessment (HI/MED/LO)  
✅ Risk tier color-coding  
✅ Export results to CSV  
✅ Error handling per row  
✅ Download example CSV  
✅ Dark theme optimized for readability

---

## Next Steps

1. **Open:** `FrontEnd/dashboard.html`
2. **Start API:** `uvicorn API.main:app --reload`
3. **Predict:** Fill form or upload CSV
4. **Export:** Download results if needed

For detailed guide: See [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md)

---

**Version:** 1.0  
**API Required:** http://localhost:8000
