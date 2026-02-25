# Genivra Dashboard - User Guide

## Quick Start

### 1. Start the API
```bash
cd c:\Users\andre\Downloads\Projects\Genivra.ai
uvicorn API.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Open the Dashboard
Open `FrontEnd/dashboard.html` in your browser or serve it via HTTP:
```bash
# Option 1: Direct file open
start FrontEnd/dashboard.html

# Option 2: Use Python simple server
python -m http.server 8001 --directory FrontEnd
# Then visit: http://localhost:8001/dashboard.html
```

---

## Features Overview

### Single Trial Prediction Tab

**Form Sections:**

1. **Trial Design**
   - Phase (Phase 1-4)
   - Indication (Alzheimer's, Parkinson's, etc.)
   - Design Type (RCT, Open Label, Double Blind)
   - Sample Size (number of participants)
   - Duration (weeks)
   - Mean Age (average participant age)

2. **Primary Endpoints**
   - Endpoint Type (objective/subjective/mixed)
   - Endpoint Name (CDR-SB, ADAS-Cog, ADCOMS, MMSE, UPDRS)
   - Variability (expected measurement variation)
   - Description (free text)

3. **Biomarker Enrichment** (Optional)
   - Select biomarkers: Amyloid PET, Tau, MRI, CSF, Blood, ApoE4
   - Input biomarker values:
     - Beta-Amyloid (pg/mL)
     - Phosphorylated Tau (pg/mL)
     - Total Tau (pg/mL)
     - Brain Atrophy (% per year)

4. **Enrollment Parameters** (Optional)
   - Female Enrollment %
   - ApoE4 Carriers %
   - Dropout Rate %

**Results Display:**
- Success Probability (percentage)
- Risk Tier (LOW/MEDIUM/HIGH) with color coding
- Confidence Flag (LOW/MEDIUM/HIGH)
- Top 5 Feature Drivers (with influence %)
- Biomarker Impact explanation

---

### Batch Predictions Tab

**Upload Options:**
1. Click drag-drop area
2. Drag CSV file onto the area
3. Use "Choose File" button

**CSV Format:**
Expected columns:
- `trial_sample_size` (integer, required)
- `trial_duration_weeks` (integer, required)
- `endpoint_type` (string: objective/subjective/mixed, required)
- `primary_endpoint_name` (string, required)
- `age_mean` (float, required)
- Optional: `phase`, `indication`, `trial_design`, `endpoint_variability`, `beta_amyloid`, `phosphorylated_tau`, `total_tau`, `brain_atrophy_rate`, `female_percent`, `apoe4_percent`, `dropout_rate`

**Download Example CSV:**
- Click "Download Example CSV" button to get sample data with 5 trials
- Each row represents one trial
- Shows all column types (required, optional, missing values)

**Results Table:**
| Column | Description |
|--------|-------------|
| Row | CSV row number (1-indexed, header = row 1) |
| Trial Name | Optional name for tracking |
| Status | ✓ Success or ✗ Error |
| Success Probability | Predicted success percentage (with visual bar) |
| Risk Tier | LOW/MEDIUM/HIGH |
| Confidence | LOW/MEDIUM/HIGH |
| Message | Error details or confirmation |

**Export Results:**
- Click "Export as CSV" to download results
- CSV contains all prediction results with timestamps
- Can be reopened in Excel or reimported

---

## Example Workflows

### Single Prediction
1. Fill form with trial parameters
2. Click "Predict Trial Success"
3. View results immediately (probability, risk, drivers)
4. Modify parameters and re-predict as needed

### Batch Processing
1. Prepare CSV with multiple trials
2. Use "Download Example CSV" to see format
3. Upload via drag-drop or file selector
4. System processes each row independently
5. View results table
6. Export to CSV for further analysis

### Error Handling
- **Missing required fields:** Red error message shows which fields are needed
- **Invalid CSV:** Error message explains issue (wrong columns, malformed)
- **Bad predictions:** Individual rows show error message without blocking batch
- **API connection:** Status badge shows "✓ Connected" when ready

---

## Data Entry Tips

### Biomarker Values
- Typical ranges (Alzheimer's):
  - Beta-Amyloid: 500-1200 pg/mL
  - Phosphorylated Tau: 40-100 pg/mL
  - Total Tau: 150-400 pg/mL
  - Brain Atrophy: 0.3-1.5 %/year

### Sample Sizes
- Phase 1: 20-100
- Phase 2: 50-300
- Phase 3: 300-1000+

### Enrollment Demographics
- Female %: 40-60% typical
- ApoE4 carriers: 40-75% (Alzheimer's trials)
- Dropout rate: 5-25% typical

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to API" | Ensure API running: `uvicorn API.main:app --reload` |
| CSV upload fails | Verify file is .csv and contains required columns |
| No results appear | Check API logs for errors; try single prediction first |
| "Missing required field" | Fill all fields in Trial Design section |
| Batch row fails but others succeed | Check that specific row for data issues; re-upload |

---

## Browser Support

✓ Chrome/Chromium (recommended)
✓ Firefox
✓ Safari
✓ Edge

Minimum: Modern ES6-compatible browser

---

## Dashboard Specs

- **Single Trial:** Form processing ~1-2 seconds
- **Batch Processing:** ~0.3 seconds per trial
  - 10 trials: ~3 seconds
  - 50 trials: ~15 seconds
  - 100+ trials: ~30 seconds
- **API Response:** JSON structured data with nested drivers/biomarkers
- **Export:** CSV with full results + error details

---

## Advanced Features

### Feature Drivers
Each prediction includes top 5 drivers showing which factors most influenced the risk assessment.

Example drivers:
- `trial_duration_weeks` (85% influence)
- `age_mean` (78% influence)
- `endpoint_variability` (65% influence)
- etc.

### Biomarker Explanation
Personalized text explaining how selected biomarkers affected the prediction.

Example: "Trial significantly strengthened by amyloid PET enrichment with high positivity rate, but limited by suboptimal tau coverage."

### Confidence Flags
- **HIGH:** All required data present, biomarkers included
- **MEDIUM:** Core data present, some biomarkers missing
- **LOW:** Minimal data, no biomarkers

---

## Integration Options

The dashboard can be:
1. Standalone HTML (current)
2. Embedded in healthcare system
3. Deployed as Docker container
4. Integrated with customer portal
5. Used with API keys for authentication

---

**Dashboard Version:** 1.0.0  
**Last Updated:** February 24, 2026  
**API Endpoint:** http://localhost:8000
