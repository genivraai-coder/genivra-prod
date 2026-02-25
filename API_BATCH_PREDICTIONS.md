# Genivra API: Batch Prediction Guide

**Endpoint:** `POST /predict_batch`  
**Alternative:** `POST /predict_batch_csv` (returns CSV directly)  
**Version:** 1.0.0 | **Date:** February 24, 2026

---

## Overview

Process multiple clinical trials in a single request by uploading a CSV file. Each row represents one trial and is validated independently. Invalid rows are skipped with error messages, while valid rows are scored.

**Key Features:**
- ✅ Process 100+ trials in seconds
- ✅ Per-row error handling (don't fail on one bad row)
- ✅ Return results as JSON or downloadable CSV
- ✅ Non-blocking async processing
- ✅ Confidence assessment per trial
- ✅ Complete audit trail in results

---

## Quick Start

### Step 1: Prepare CSV File

Column format (see example below):
```csv
trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean,...
```

**Required columns:**
- `trial_sample_size` (integer > 0)
- `trial_duration_weeks` (integer > 0)
- `endpoint_type` ('objective', 'subjective', or 'mixed')
- `primary_endpoint_name` (string)
- `age_mean` (number)

**Optional columns:**
- `trial_name` - Identifier for your records
- `baseline_mmse`, `baseline_moca`, `cdr_baseline` - Cognitive scores
- `apoe_e4_carrier`, `ptau217_high`, `amyloid_pet_positive` - Biomarkers (0 or 1)
- `phase`, `indication`, `number_of_arms` - Trial metadata

### Step 2: Upload CSV

#### Using Python Requests:
```python
import requests

with open("trials.csv", "rb") as f:
    files = {"file": ("trials.csv", f, "text/csv")}
    response = requests.post(
        "http://localhost:8000/predict_batch",
        files=files,
        params={"return_csv": False}  # Return JSON
    )

results = response.json()
print(f"Processed: {results['total_rows']} trials")
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")

# Show first result
first = results['results'][0]
print(f"Trial {first['trial_name']}: {first['trial_success_probability']:.1%} success")
```

#### Using cURL:
```bash
# Return JSON response
curl -X POST http://localhost:8000/predict_batch \
  -F "file=@trials.csv"

# Return CSV file for download
curl -X POST http://localhost:8000/predict_batch \
  -F "file=@trials.csv" \
  -G --data-urlencode "return_csv=true" \
  -o predictions.csv
```

#### Using Web Form (Swagger UI):
1. Go to http://localhost:8000/docs
2. Find "POST /predict_batch"
3. Click "Try it out"
4. Click "Choose File" and select your CSV
5. Click "Execute"
6. View results below

---

## CSV Format

### Minimal CSV (Required Fields Only)
```csv
trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean
200,52,objective,CDR-SB,72.5
150,26,objective,ADAS-Cog,70.0
300,52,subjective,ADCOMS,73.0
```

### Complete CSV (All Fields)
```csv
trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean,baseline_mmse,baseline_moca,cdr_baseline,biomarker_enrichment_strategy,apoe_e4_carrier,apoe_e4_homozygous,ptau217_high,ptau217_continuous,csf_abeta42_40_ratio_low,csf_abeta42_40_ratio_continuous,csf_ptau_elevated,amyloid_pet_positive,tau_pet_positive,hippocampal_atrophy_mri,hippocampal_atrophy_binary,phase,indication,number_of_arms,randomization_ratio
TRIAL-001,200,52,objective,CDR-SB,72.5,22.0,21.5,1.5,at_positive,1,0,1,18.5,1,0.45,0,1,1,3800.0,1,Phase II,Alzheimers Disease,2,1:1
TRIAL-002,150,26,objective,ADAS-Cog,70.0,24.0,23.0,1.0,at_positive,0,0,1,16.2,1,0.48,1,1,0,4100.0,0,Phase II,Alzheimers Disease,2,1:1
TRIAL-003,300,52,subjective,ADCOMS,73.0,20.0,19.5,2.0,cognitive_only,1,1,0,12.1,0,0.52,0,0,1,3600.0,1,Phase II,Alzheimers Disease,3,1:1:1
```

### Field Details

| Column | Type | Required | Valid Range | Example |
|--------|------|----------|-------------|---------|
| **trial_name** | string | No | any | "TRIAL-001", "AD-2026-001" |
| **trial_sample_size** | integer | ✅ Yes | > 0 | 100, 200, 500 |
| **trial_duration_weeks** | integer | ✅ Yes | > 0 | 26, 52, 78 |
| **endpoint_type** | string | ✅ Yes | objective, subjective, mixed | "objective" |
| **primary_endpoint_name** | string | ✅ Yes | any | "CDR-SB", "ADAS-Cog" |
| **age_mean** | number | ✅ Yes | any | 70.5, 72.0 |
| **baseline_mmse** | number | No | 0-30 | 22.0, 24.5 |
| **baseline_moca** | number | No | 0-30 | 21.5, 23.0 |
| **cdr_baseline** | number | No | 0-18 | 0.5, 1.5 |
| **apoe_e4_carrier** | integer | No | 0 or 1 | 1 |
| **apoe_e4_homozygous** | integer | No | 0 or 1 | 0 |
| **ptau217_high** | integer | No | 0 or 1 | 1 |
| **ptau217_continuous** | number | No | any | 18.5, 15.2 |
| **csf_abeta42_40_ratio_low** | integer | No | 0 or 1 | 1 |
| **csf_abeta42_40_ratio_continuous** | number | No | any | 0.45, 0.52 |
| **csf_ptau_elevated** | integer | No | 0 or 1 | 0 |
| **amyloid_pet_positive** | integer | No | 0 or 1 | 1 |
| **tau_pet_positive** | integer | No | 0 or 1 | 1 |
| **hippocampal_atrophy_mri** | number | No | any | 3800.0, 4100.0 |
| **hippocampal_atrophy_binary** | integer | No | 0 or 1 | 1 |
| **biomarker_enrichment_strategy** | string | No | any | "at_positive", "cognitive_only" |
| **phase** | string | No | any | "Phase II" |
| **indication** | string | No | any | "Alzheimers Disease" |
| **number_of_arms** | integer | No | > 0 | 2, 3 |
| **randomization_ratio** | string | No | any | "1:1", "1:1:1" |

---

## Response Formats

### JSON Response (Default)

**Status:** 200 OK

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
      "trial_success_probability": 0.85,
      "risk_tier": "LOW",
      "biomarker_explanation": "This trial enrolls participants with...",
      "confidence_flag": "HIGH",
      "top_drivers": [
        {
          "feature_name": "trial_sample_size",
          "coefficient": 1.422,
          "direction": "positive",
          "impact_magnitude": 1.422
        }
      ],
      "error_message": null,
      "error_fields": null
    },
    {
      "row_number": 3,
      "trial_name": "TRIAL-002",
      "success": true,
      "trial_success_probability": 0.72,
      "risk_tier": "MEDIUM",
      "biomarker_explanation": "...",
      "confidence_flag": "MEDIUM",
      "top_drivers": [...],
      "error_message": null,
      "error_fields": null
    },
    {
      "row_number": 4,
      "trial_name": "TRIAL-003",
      "success": false,
      "trial_success_probability": null,
      "risk_tier": null,
      "biomarker_explanation": null,
      "confidence_flag": null,
      "top_drivers": null,
      "error_message": "Missing required field: trial_sample_size",
      "error_fields": null
    }
  ],
  "model_version": "v1.0",
  "generated_timestamp": "2026-02-24T18:30:45.123456Z"
}
```

### CSV Response

**Query:** `?return_csv=true`  
**HTTP:** 200 OK with `Content-Disposition: attachment`

```csv
row_number,trial_name,success,trial_success_probability,risk_tier,confidence_flag,error_message
2,TRIAL-001,True,0.85,LOW,HIGH,
3,TRIAL-002,True,0.72,MEDIUM,MEDIUM,
4,TRIAL-003,False,,,,Missing required field: trial_sample_size
```

---

## Error Handling

### Row-Level Errors (Processed anyway, included in response)

```json
{
  "row_number": 4,
  "trial_name": "TRIAL-003",
  "success": false,
  "error_message": "Missing required field: trial_sample_size",
  "error_fields": null
}
```

**Examples:**
| Error | Cause | Fix |
|-------|-------|-----|
| Missing required field: trial_sample_size | Column not in CSV | Add column |
| Invalid value for endpoint_type | Not 'objective', 'subjective', or 'mixed' | Use valid enum |
| Out of range for baseline_mmse | MMSE > 30 or < 0 | Use value 0-30 |
| Unexpected error: invalid literal for int() | String like "two-hundred" | Use numeric value |

### File-Level Errors (HTTP response)

| Status | Error | Cause |
|--------|-------|-------|
| 400 | "File must be CSV format (.csv)" | Wrong file type |
| 400 | "CSV file is empty" | No rows in CSV |
| 400 | "Invalid CSV format: ..." | Malformed CSV (missing quotes, etc.) |
| 413 | Request entity too large | File > size limit |

---

## Usage Examples

### Example 1: Python - Process and Save Results

```python
import requests
import json

# Load trials
with open("trials.csv", "rb") as f:
    files = {"file": ("trials.csv", f, "text/csv")}
    response = requests.post(
        "http://localhost:8000/predict_batch",
        files=files
    )

data = response.json()

# Summary
print(f"Processed {data['total_rows']} trials")
print(f"  ✅ Successful: {data['successful']}")
print(f"  ❌ Failed: {data['failed']}")
print()

# Show results
for result in data['results']:
    if result['success']:
        print(f"✅ {result['trial_name']}")
        print(f"   Probability: {result['trial_success_probability']:.1%}")
        print(f"   Risk Tier: {result['risk_tier']}")
    else:
        print(f"❌ {result['trial_name']}")
        print(f"   Error: {result['error_message']}")

# Save results
with open("predictions.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Example 2: Bash - Download as CSV

```bash
# Upload trials, get CSV download
curl -X POST http://localhost:8000/predict_batch \
  -F "file=@trials.csv" \
  -G --data-urlencode "return_csv=true" \
  -o predictions.csv

echo "Results saved to predictions.csv"
```

### Example 3: Python with Pandas

```python
import pandas as pd
import requests

# Read input CSV
input_df = pd.read_csv("trials.csv")

# Upload for batch prediction
with open("trials.csv", "rb") as f:
    files = {"file": ("trials.csv", f, "text/csv")}
    response = requests.post(
        "http://localhost:8000/predict_batch",
        files=files,
        params={"return_csv": True}
    )

# Save as CSV
with open("predictions.csv", "wb") as f:
    f.write(response.content)

# Load and analyze
results_df = pd.read_csv("predictions.csv")
print(results_df[['trial_name', 'success', 'trial_success_probability', 'risk_tier']])

# Get summary
print(f"\nSuccess Rate: {results_df['success'].sum() / len(results_df) * 100:.1f}%")
print(f"Average Probability: {results_df['trial_success_probability'].mean():.1%}")
```

---

## Performance

- **Speed:** ~0.3 seconds per trial
- **Capacity:** Tested with 1000+ trials
- **Memory:** ~100MB + file size
- **Non-blocking:** Uses async processing

### Performance Examples

| Trials | Time | Memory |
|--------|------|--------|
| 10 | ~3 sec | 150 MB |
| 100 | ~30 sec | 200 MB |
| 500 | ~2.5 min | 350 MB |
| 1000 | ~5 min | 500 MB |

---

## Download Example CSV

Download the example file: [examples_batch_predictions.csv](examples_batch_predictions.csv)

Contains 10 realistic examples covering:
- ✅ Complete data rows
- ⚠️ Partial missing data
- ❌ Invalid data patterns

---

## Integration Example: Healthcare Database

```python
import pandas as pd
import requests
from sqlalchemy import create_engine

# Connect to database
engine = create_engine('postgresql://user:pass@localhost/trials_db')

# Get pending trials
trials_df = pd.read_sql(
    "SELECT * FROM trials WHERE status='pending' LIMIT 100",
    engine
)

# Export to CSV
trials_df.to_csv("pending_trials.csv", index=False)

# Batch predict
with open("pending_trials.csv", "rb") as f:
    files = {"file": ("pending_trials.csv", f, "text/csv")}
    response = requests.post(
        "http://api.genivra.ai/predict_batch",
        files=files,
        params={"return_csv": False}
    )

results = response.json()

# Store predictions
for result in results['results']:
    if result['success']:
        pd.DataFrame([{
            'trial_id': result['trial_name'],
            'success_probability': result['trial_success_probability'],
            'risk_tier': result['risk_tier'],
            'confidence': result['confidence_flag'],
            'processed_at': result['generated_timestamp']  # Use timestamp from result
        }]).to_sql('predictions', engine, if_exists='append', index=False)

print(f"Stored {results['successful']} predictions")
```

---

## Troubleshooting

### Issue: "CSV file is empty"
**Solution:** Ensure CSV has at least one data row (headers don't count)

### Issue: "Invalid value for endpoint_type"
**Solution:** Check that endpoint_type is exactly: 'objective', 'subjective', or 'mixed'

### Issue: "Out of range for baseline_mmse"
**Solution:** MMSE must be between 0 and 30 (blank/empty is OK if not provided)

### Issue: Some rows succeed, one fails
**Solution:** Check the error_message for that row in results. Invalid rows don't block others.

### Issue: File upload hangs
**Solution:** 
- Check file size (should be < 10MB)
- Verify CSV formatting (no unclosed quotes)
- Try smaller batch (< 100 rows) first

---

## REST API Reference

### POST /predict_batch

**Parameters:**
- `file` (form): CSV file upload (required)
- `return_csv` (query): Return CSV instead of JSON (optional, default=false)

**Request:**
```bash
curl -X POST http://localhost:8000/predict_batch \
  -F "file=@trials.csv" \
  -G --data-urlencode "return_csv=false"
```

**Response:** 200 OK (JSON or CSV)

---

### POST /predict_batch_csv

**Alias for:** `/predict_batch?return_csv=true`

**Parameters:**
- `file` (form): CSV file upload (required)

**Request:**
```bash
curl -X POST http://localhost:8000/predict_batch_csv \
  -F "file=@trials.csv" \
  -o predictions.csv
```

**Response:** 200 OK (CSV file download)

---

## Best Practices

✅ **DO:**
- Use meaningful trial_name values for tracking
- Include optional fields (biomarkers) when available for better confidence
- Test with small CSV first (5-10 rows)
- Handle per-row errors (don't assume all succeed)
- Use JSON response for processing, CSV for reporting
- Keep CSV files < 10MB

❌ **DON'T:**
- Leave required fields blank (trial_sample_size, endpoint_type, etc.)
- Mix data types in columns (all numbers or all strings)
- Use special characters in trial_name without quotes
- Forget to specify endpoint_type as one of the 3 valid values
- Assume failures = bad API (check error_message in result)

---

## What's Next?

- ✅ Batch predictions working
- 📊 Export results to Excel/dashboard
- 💾 Store predictions in database
- 📧 Email reports automatically
- 🔔 Set up alerts for high-risk trials

---

*Genivra API - CNS Clinical Trial Risk Scoring Engine*  
*Version 1.0.0 | February 24, 2026*
