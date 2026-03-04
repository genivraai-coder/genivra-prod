# Genivra Dashboard Integration Guide

## Overview

The Genivra HTML dashboards are now fully connected to the consolidated FastAPI endpoints. Users can:

1. **Single Trial Prediction** - Submit one trial and get instant risk assessment
2. **Batch Processing** - Upload CSV with multiple trials for bulk predictions
3. **Results Visualization** - View probability, risk tier, feature drivers, and biomarker explanations

---

## Files

### New/Updated Files

| File | Purpose |
|------|---------|
| `dashboards/predict.html` | New comprehensive prediction interface (single trial + batch) |
| `dashboards/upload.html` | Updated batch CSV upload tool (now uses `/predict_batch` endpoint) |
| `dashboards/dashboard.html` | Results visualization dashboard |
| `dashboards/index.html` | Landing page |

---

## Quick Start

### 1. Start the API

```bash
cd Genivra.ai
uvicorn api.main:app --reload
```

The API will be available at: `http://localhost:8000`

### 2. Open the Dashboard

**Option A: Single Trial + Batch Interface (Recommended)**
```
http://localhost:8000/static/predict.html
```

**Option B: Batch Upload Tool Only**
```
http://localhost:8000/static/upload.html
```

**Option C: Results Dashboard**
```
http://localhost:8000/static/dashboard.html
```

### 3. Use Available Demo API Keys

```
Tier 1 (100 req/month):  demo_tier1_key_12345
Tier 2 (unlimited):      demo_tier2_key_67890
```

---

## Features

### Single Trial Prediction Form (`predict.html` - Tab 1)

**Sections:**
1. **Trial Design** - Phase, indication, sample size, duration, arms, randomization
2. **Primary Endpoint** - Objective or subjective endpoint specification
3. **Patient Population** - Age, cognitive baselines (MMSE, MoCA, CDR)
4. **Biomarkers** - Checkbox selection for 8 binary biomarkers
5. **Enrichment Strategy** - Patient selection criteria

**Results Display:**
- ✅ Success probability (0-1)
- ✅ Risk tier (HIGH/MEDIUM/LOW)
- ✅ Top 3 feature drivers with impact magnitude
- ✅ Biomarker explanation (natural language)
- ✅ Confidence flag (HIGH/MEDIUM/LOW)
- ✅ Model version and timestamp

### Batch Processing (`predict.html` - Tab 2 or `upload.html`)

**Workflow:**
1. Upload CSV file with trial data
2. Required columns:
   - `trial_sample_size` (integer)
   - `trial_duration_weeks` (integer)
   - `endpoint_type` (string: "objective" or "subjective")
   - `primary_endpoint_name` (string)
   - `age_mean` (float)

3. Optional columns:
   - All biomarker fields (0 or 1)
   - `phase`, `indication`, `trial_name`
   - Enrollment data: `baseline_mmse`, `baseline_moca`, `cdr_baseline`

**Features:**
- Drag & drop file upload
- Real-time progress updates
- Per-row error handling
- Download results as CSV
- Summary statistics (total, successful, failed)

### Results Display

**Single Trial:**
- Large probability display with gradient
- Risk tier color-coded badge
- Feature importance visualization with bars
- Detailed biomarker explanation section

**Batch:**
- Summary statistics (count boxes)
- Results table with status icons
- Downloadable CSV export
- Row-by-row error messages

---

## API Integration Details

### Authentication

All requests require the `x-api-key` header:

```javascript
fetch('/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'x-api-key': 'demo_tier1_key_12345',
    },
    body: JSON.stringify(payload),
})
```

### Single Trial Endpoint: POST /predict

**Request Format:**
```json
{
    "phase": "Phase II",
    "indication": "Alzheimer's Disease",
    "trial_design": {
        "phase": "Phase II",
        "indication": "Alzheimer's Disease",
        "trial_sample_size": 150,
        "trial_duration_weeks": 52,
        "number_of_arms": 2,
        "randomization_ratio": "1:1"
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {
        "apoe_e4_carrier": 1,
        "ptau217_high": 1,
        "amyloid_pet_positive": 1,
        "apoe_e4_homozygous": null,
        "ptau217_continuous": null
    },
    "enrollment": {
        "age_mean": 70.0,
        "baseline_mmse": 20.0,
        "baseline_moca": null,
        "cdr_baseline": 1.0
    },
    "biomarker_enrichment_strategy": "at_positive"
}
```

**Response Format:**
```json
{
    "trial_success_probability": 0.92,
    "risk_tier": "LOW",
    "top_drivers": [
        {
            "feature_name": "amyloid_pet_positive",
            "coefficient": 2.45,
            "direction": "positive",
            "impact_magnitude": 2.45
        }
    ],
    "biomarker_explanation": "Amyloid PET positivity is a strong indicator...",
    "confidence_flag": "HIGH",
    "missing_biomarker_count": 3,
    "model_version": "v2.0-consolidated",
    "generated_timestamp": "2026-03-03T10:30:00Z"
}
```

### Batch Upload Endpoint: POST /predict_batch

**Request Format:**
- Multipart form data with CSV file
- URL parameter: `?return_csv=false` (for JSON response)

**Response Format:**
```json
{
    "total_rows": 3,
    "successful": 2,
    "failed": 1,
    "results": [
        {
            "row_number": 2,
            "trial_name": "TRIAL-001",
            "success": true,
            "trial_success_probability": 0.92,
            "risk_tier": "LOW",
            "confidence_flag": "HIGH",
            "error_message": null
        },
        {
            "row_number": 3,
            "trial_name": "TRIAL-002",
            "success": false,
            "trial_success_probability": null,
            "risk_tier": null,
            "confidence_flag": null,
            "error_message": "Missing required field: trial_sample_size"
        }
    ],
    "generated_timestamp": "2026-03-03T10:35:00Z"
}
```

---

## Example CSV Format

```csv
trial_name,phase,indication,trial_sample_size,trial_duration_weeks,number_of_arms,randomization_ratio,endpoint_type,primary_endpoint_name,age_mean,baseline_mmse,baseline_moca,cdr_baseline,apoe_e4_carrier,ptau217_high,amyloid_pet_positive,tau_pet_positive,hippocampal_atrophy_binary,biomarker_enrichment_strategy
LECANEMAB-2,Phase II,Alzheimer's Disease,150,52,2,1:1,objective,CDR-SB,70.0,20.0,,1.0,1,1,1,1,1,at_positive
HIGH-RISK,Phase II,Alzheimer's Disease,50,12,2,1:1,subjective,MMSE,65.0,26.0,28.0,0.5,0,0,0,0,0,cognitive_only
PLACEBO-CTL,Phase III,Mild Cognitive Impairment,200,104,2,1:1,objective,MMSE,75.0,22.0,,1.0,1,,1,,0,at_positive
```

---

## Troubleshooting

### Common Issues

**"Missing x-api-key header"**
- Solution: Enter a valid API key in the API Key field at the top

**"Invalid or inactive API key"**
- Solution: Use one of the demo keys: `demo_tier1_key_12345` or `demo_tier2_key_67890`
- Or create a new key using the admin endpoints

**"Monthly limit exceeded"**
- Solution: Use `demo_tier2_key_67890` for unlimited requests (for demo purposes)
- Or wait for next month billing cycle

**"Missing required field: trial_sample_size"**
- Solution: Ensure CSV has required columns (see CSV Format above)
- Verify column names match exactly (case-sensitive)

**CORS Error**
- Solution: Ensure API is running with CORS middleware enabled (default in consolidated API)
- Check that you're accessing via `http://localhost:8000` (not `http://127.0.0.1:8000`)

### Validation Rules

| Field | Type | Required | Range/Notes |
|-------|------|----------|------------|
| trial_sample_size | integer | ✅ | > 0 |
| trial_duration_weeks | integer | ✅ | > 0 |
| endpoint_type | string | ✅ | "objective" or "subjective" |
| primary_endpoint_name | string | ✅ | e.g., "CDR-SB", "MMSE" |
| age_mean | float | ✅ | >= 0 |
| phase | string | ❌ | "Phase I/II/III/IV" |
| indication | string | ❌ | Clinical indication |
| biomarkers | object | ❌ | Binary (0/1) or null |
| enrollment | object | ❌ | MMSE/MoCA: 0-30, CDR: 0-3 |

---

## Advanced Usage

### Creating Custom API Keys

Use the admin endpoints to create additional API keys with rate limits:

```bash
curl -X POST "http://localhost:8000/admin/api-keys/create?api_key=custom_key_xyz&tier=tier_2&name=Customer%20ABC&org=ABC%20Corp"
```

### Monitoring API Usage

```bash
curl "http://localhost:8000/admin/api-keys/list" \
  -H "x-api-key: demo_tier1_key_12345"
```

### Changing Host/Port

If hosting elsewhere, update the `API_BASE_URL` in JavaScript:

```javascript
const API_BASE_URL = 'https://api.genivra.example.com';
```

---

## Performance Notes

- **Single Trial**: ~200-500ms typical response time
- **Batch Processing**: ~100-200ms per trial (parallelization on server)
- **File Upload Size**: Max 10 MB (configurable)
- **Concurrent Requests**: Use rate limiting based on tier

---

## UI Features

### Design System
- Dark theme with cyan/purple/pink gradient accent
- Responsive grid layout (mobile-friendly)
- Smooth animations and transitions
- Accessible form inputs with visual feedback

### Components
- **Form Sections**: Organized into logical groups
- **Status Messages**: Color-coded (loading, error, success)
- **Results Cards**: Highlightable with gradient backgrounds
- **Data Tables**: Sortable with hover effects
- **Progress Indicators**: Real-time status during processing

---

## Future Enhancements

Potential additions:
- [ ] Export results to PDF
- [ ] Saved predictions history
- [ ] Comparison tool (multiple trials side-by-side)
- [ ] Advanced filtering/sorting
- [ ] Integration with trial databases
- [ ] WebSocket for real-time batch updates
- [ ] Dark/light theme toggle
- [ ] Multi-language support

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review API logs: `http://localhost:8000/docs` (Swagger UI)
3. Check browser console for JavaScript errors (F12)
4. Verify API is running and accessible

---

**Version**: 2.0 (Consolidated)  
**Last Updated**: March 3, 2026  
**API Version**: Same domain (relative URLs)
