# ✅ IMPLEMENTATION CHECKLIST
## Frontend Requirements for Successful Prediction Requests

**Project:** Genivra CNS Risk Intelligence Platform  
**Component:** Frontend Integration with FastAPI Backend  
**Prepared:** June 2, 2026  
**Status:** Ready for Implementation

---

## SECTION 1: REQUIRED FORM FIELDS

### ✅ CRITICAL FIELDS (Must have or request fails)

#### Trial Design - Sample Size
- [ ] HTML input: `<input name="trial_design.trial_sample_size" type="number" min="1" required />`
- [ ] Must convert to integer before sending
- [ ] Example: `200`
- [ ] Validation: > 0
- [ ] Error if missing: ✅ Request will fail with 400

#### Trial Design - Duration
- [ ] HTML input: `<input name="trial_design.trial_duration_weeks" type="number" min="1" required />`
- [ ] Must convert to integer before sending
- [ ] Example: `52`
- [ ] Validation: > 0
- [ ] Error if missing: ✅ Request will fail with 400

#### Endpoints - Type
- [ ] HTML input: `<select name="endpoint_type" required>`
- [ ] Valid values ONLY: `"objective"`, `"subjective"`, `"mixed"` (lowercase)
- [ ] Example: `objective`
- [ ] Validation: Must be one of three values
- [ ] Error if missing: ✅ Request will fail with 400

#### Endpoints - Primary Endpoint Name
- [ ] HTML input: `<input name="primary_endpoint_name" type="text" required />`
- [ ] Any string accepted (CDR-SB, ADAS-Cog, MMSE, etc.)
- [ ] Example: `CDR-SB`
- [ ] Validation: Cannot be empty
- [ ] Error if missing: ✅ Request will fail with 400

#### Enrollment - Age Mean
- [ ] HTML input: `<input name="age_mean" type="number" step="0.1" required />`
- [ ] Must convert to float before sending
- [ ] Example: `72.5`
- [ ] Validation: > 0
- [ ] Error if missing: ✅ Request will fail with 400

### ⭐ CONDITIONAL FIELDS (Optional but improve confidence)

**For HIGH confidence (missing_biomarker_count = 0):**
- [ ] `apoe_e4_carrier` (0 or 1)
- [ ] `apoe_e4_homozygous` (0 or 1)
- [ ] `ptau217_high` (0 or 1)
- [ ] `csf_abeta42_40_ratio_low` (0 or 1)
- [ ] `csf_ptau_elevated` (0 or 1)
- [ ] `amyloid_pet_positive` (0 or 1)
- [ ] `tau_pet_positive` (0 or 1)
- [ ] `hippocampal_atrophy_binary` (0 or 1)
- [ ] `baseline_mmse` (0-30)
- [ ] `baseline_moca` (0-30)
- [ ] `cdr_baseline` (0-18)

**For MEDIUM confidence (missing_biomarker_count <= 2):**
- [ ] Include at least 9 of the 11 above fields

**For LOW confidence (missing_biomarker_count >= 3):**
- [ ] Include fewer than 9 fields is acceptable but not recommended

### ❌ OPTIONAL FIELDS (Can omit safely)

- [ ] `trial_design.number_of_arms` - Defaults to null
- [ ] `trial_design.randomization_ratio` - Defaults to null
- [ ] `trial_design.phase` - Defaults to null
- [ ] `trial_design.indication` - Defaults to null
- [ ] `ptau217_continuous` - Defaults to null
- [ ] `csf_abeta42_40_ratio_continuous` - Defaults to null
- [ ] `hippocampal_atrophy_mri` - Defaults to null
- [ ] `baseline_moca` - Defaults to null
- [ ] `biomarker_enrichment_strategy` - Defaults to "unknown"

---

## SECTION 2: JSON STRUCTURE VALIDATION

### ✅ Required Top-Level Sections

```javascript
// MUST have these exact keys
{
  "trial_design": { /* object */ },
  "endpoints": { /* object */ },
  "biomarkers": { /* object */ },
  "enrollment": { /* object */ }
}
```

- [ ] `trial_design` section present: ✅ MUST HAVE
- [ ] `endpoints` section present: ✅ MUST HAVE
- [ ] `biomarkers` section present: ✅ MUST HAVE (can be empty {})
- [ ] `enrollment` section present: ✅ MUST HAVE

### ✅ Field Type Conversions (Critical!)

| Field | HTML Type | JSON Type | Conversion |
|-------|-----------|-----------|-----------|
| trial_sample_size | number | int | `parseInt(value, 10)` |
| trial_duration_weeks | number | int | `parseInt(value, 10)` |
| number_of_arms | number | int | `parseInt(value, 10)` |
| age_mean | number | float | `parseFloat(value)` |
| baseline_mmse | number | float | `parseFloat(value)` |
| baseline_moca | number | float | `parseFloat(value)` |
| cdr_baseline | number | float | `parseFloat(value)` |
| ptau217_continuous | number | float | `parseFloat(value)` |
| csf_abeta42_40_ratio_continuous | number | float | `parseFloat(value)` |
| hippocampal_atrophy_mri | number | float | `parseFloat(value)` |
| apoe_e4_carrier | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| apoe_e4_homozygous | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| ptau217_high | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| csf_abeta42_40_ratio_low | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| csf_ptau_elevated | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| amyloid_pet_positive | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| tau_pet_positive | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| hippocampal_atrophy_binary | checkbox | int (0/1) | `input.checked ? 1 : 0` |
| endpoint_type | select | string | keep as-is (lowercase) |
| primary_endpoint_name | text | string | keep as-is |
| randomization_ratio | text | string | keep as-is |
| phase | text | string | keep as-is |
| indication | text | string | keep as-is |
| biomarker_enrichment_strategy | select | string | keep as-is |

- [ ] All integers converted with `parseInt(value, 10)`
- [ ] All floats converted with `parseFloat(value)`
- [ ] All checkboxes converted to 0/1 using ternary
- [ ] All strings lowercased (especially endpoint_type)
- [ ] Empty strings omitted from final JSON

### ✅ Example Valid JSON to Send

```javascript
// Minimal (will work, LOW confidence)
{
  "trial_design": {
    "trial_sample_size": 200,
    "trial_duration_weeks": 52
  },
  "endpoints": {
    "endpoint_type": "objective",
    "primary_endpoint_name": "CDR-SB"
  },
  "biomarkers": {},
  "enrollment": {
    "age_mean": 72.5
  }
}

// Complete (HIGH confidence)
{
  "phase": "Phase II",
  "indication": "Alzheimer's Disease",
  "trial_design": {
    "trial_sample_size": 200,
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
    "apoe_e4_homozygous": 0,
    "ptau217_high": 1,
    "amyloid_pet_positive": 1,
    "tau_pet_positive": 0,
    "hippocampal_atrophy_binary": 1
  },
  "enrollment": {
    "age_mean": 72.5,
    "baseline_mmse": 22.0,
    "baseline_moca": 19.0,
    "cdr_baseline": 1.5
  },
  "biomarker_enrichment_strategy": "at_positive"
}
```

- [ ] Trial design section has sample_size and duration_weeks
- [ ] Endpoints section has endpoint_type and primary_endpoint_name
- [ ] Enrollment section has age_mean
- [ ] All numbers are actual numbers (not strings)
- [ ] All booleans (checkboxes) are 0 or 1
- [ ] Empty optional fields omitted entirely
- [ ] No extra fields not in spec

---

## SECTION 3: API ENDPOINT DETAILS

### ✅ Endpoint Configuration

| Property | Value |
|----------|-------|
| **URL** | `http://127.0.0.1:8000/predict` |
| **HTTP Method** | `POST` |
| **Content-Type Header** | `application/json` |
| **Authentication** | Optional (dev mode) |
| **Timeout** | 30 seconds recommended |
| **CORS** | ✅ Enabled on backend |

### ✅ Request Headers Required

```javascript
headers: {
  'Content-Type': 'application/json'
  // 'x-api-key': 'your-key' // Optional in dev
}
```

- [ ] POST method used
- [ ] Content-Type: application/json header set
- [ ] URL is http://127.0.0.1:8000/predict (not HTTPS in dev)
- [ ] 30-second timeout configured
- [ ] No authentication required for /predict endpoint

### ✅ Response Expected

**Status Code:** 200 OK

```javascript
{
  "trial_success_probability": 0.72,  // float 0-1
  "risk_tier": "LOW",                 // "HIGH" | "MEDIUM" | "LOW"
  "top_drivers": [
    {
      "feature_name": "trial_sample_size",
      "coefficient": 1.422,
      "direction": "positive",        // "positive" | "negative"
      "impact_magnitude": 1.422
    },
    // ... up to 5 drivers
  ],
  "biomarker_explanation": "Natural language explanation...",
  "confidence_flag": "HIGH",          // "HIGH" | "MEDIUM" | "LOW"
  "missing_biomarker_count": 0,       // 0-11
  "model_version": "v1.0",
  "generated_timestamp": "2026-06-02T10:45:30.123456Z"  // ISO 8601 UTC
}
```

- [ ] Response status code is 200
- [ ] trial_success_probability is float between 0-1
- [ ] risk_tier is one of: HIGH, MEDIUM, LOW
- [ ] top_drivers is array with 1-5 items
- [ ] Each driver has: feature_name, coefficient, direction, impact_magnitude
- [ ] biomarker_explanation is string (not null)
- [ ] confidence_flag is one of: HIGH, MEDIUM, LOW
- [ ] missing_biomarker_count is integer 0-11
- [ ] generated_timestamp is valid ISO 8601 format

---

## SECTION 4: ERROR HANDLING SPECIFICATION

### ✅ HTTP 400 Bad Request

**When it happens:**
- Missing required field
- Invalid data type
- Invalid enum value
- Invalid JSON structure

**Response body:**
```javascript
{
  "error": "validation error",
  "message": "Missing required field: trial_sample_size",
  "status_code": 400,
  "timestamp": "2026-06-02T10:45:30Z"
}
```

**Frontend must:**
- [ ] Check `response.status !== 200`
- [ ] Parse error response
- [ ] Display `error.message` to user
- [ ] Show validation error, not generic "API error"
- [ ] Allow user to fix form and retry

### ✅ HTTP 500 Server Error

**When it happens:**
- Model not found
- Feature engineering fails
- Unexpected exception

**Response body:**
```javascript
{
  "error": "server error",
  "message": "Model prediction failed: ...",
  "status_code": 500,
  "timestamp": "2026-06-02T10:45:30Z"
}
```

**Frontend must:**
- [ ] Check `response.status !== 200`
- [ ] Show "API Server Error" message
- [ ] Suggest checking if backend is running
- [ ] Show timestamp and error code in logs
- [ ] Allow user to retry after backend restarts

### ✅ Network Errors

**When it happens:**
- API not running on localhost:8000
- Network unreachable
- Request timeout (>30 seconds)
- CORS blocked

**Frontend must:**
- [ ] Wrap fetch in try/catch
- [ ] Catch TypeError with message "Failed to fetch"
- [ ] Show "API Server Unreachable - Ensure backend is running on localhost:8000"
- [ ] Provide instructions to start backend

### ✅ Error Display UX

- [ ] Show error message in red/warning color
- [ ] Scroll to error message automatically
- [ ] Keep form data intact (don't clear)
- [ ] Show "Retry" button
- [ ] Log error to console for debugging
- [ ] Never show raw error stack traces to user

**JavaScript Example:**
```javascript
catch (error) {
  console.error('Prediction error:', error);
  
  let userMessage = error.message;
  
  if (error.message.includes('Failed to fetch')) {
    userMessage = 'API server unreachable. Ensure backend is running on localhost:8000';
  } else if (error.message.includes('400')) {
    userMessage = 'Validation error. Please check your input values.';
  } else if (error.message.includes('500')) {
    userMessage = 'Server error. Please try again in a moment.';
  }
  
  showError(userMessage);
}
```

---

## SECTION 5: DISPLAY RESULTS SPECIFICATION

### ✅ Success Probability

- [ ] Convert `trial_success_probability` from 0-1 to 0-100%
- [ ] Display with 1 decimal place: `(0.72 * 100).toFixed(1) + '%'` → "72.0%"
- [ ] Show in large, prominent font
- [ ] Optional: Use a progress bar or circular gauge
- [ ] Color match with risk tier (not separate color)

### ✅ Risk Tier Display

| Tier | Color | Background | Meaning |
|------|-------|-----------|---------|
| LOW | `#2fd9ff` (Cyan) | `rgba(47, 217, 255, 0.1)` | ✅ Likely to succeed |
| MEDIUM | `#ffa500` (Orange) | `rgba(255, 165, 0, 0.1)` | ⚠️ Uncertain outcome |
| HIGH | `#ff6b6b` (Red) | `rgba(255, 107, 107, 0.1)` | ❌ High failure risk |

- [ ] Risk tier displayed prominently below probability
- [ ] Colored badge (foreground + background)
- [ ] Text is capitalized: "LOW", "MEDIUM", "HIGH"
- [ ] Matches design system colors from genivra_final.html

### ✅ Top Drivers (Feature Importance)

**Data provided:**
```javascript
{
  "feature_name": "trial_sample_size",
  "coefficient": 1.422,
  "direction": "positive",
  "impact_magnitude": 1.422
}
```

**Display requirements:**
- [ ] Show 2-5 drivers (API returns up to 5)
- [ ] Show rank (1st, 2nd, 3rd, etc.)
- [ ] Show feature name (with underscores replaced by spaces)
- [ ] Show direction as icon: `↑` for positive, `↓` for negative
- [ ] Show coefficient to 3 decimal places
- [ ] Optional: Show impact magnitude as bar chart
- [ ] Sort by magnitude (already sorted by API)

**Example:**
```
Top Model Drivers:
1. trial sample size ↑ (coef: 1.422)
2. age mean ↓ (coef: -0.845)
3. amyloid pet positive ↑ (coef: 0.934)
4. endpoint type objective ↑ (coef: 0.567)
5. baseline mmse ↑ (coef: 0.123)
```

### ✅ Biomarker Explanation

- [ ] Display full `biomarker_explanation` text
- [ ] Format as readable paragraph (not truncated)
- [ ] Use readable font (avoid monospace)
- [ ] No additional processing needed (API returns plain English)

**Example text:**
> "This trial enrolls participants with amyloid PET positive and elevated plasma p-tau217 biomarker profile. Enrichment strategy is 'at_positive', targeting specific biomarker populations. Trial design includes adequate sample size and extended follow-up duration. Model predicts 72% success probability, indicating strong evidence for success. Primary model drivers: trial_sample_size (increases success) and amyloid_pet_positive (increases success)."

### ✅ Confidence Flag

- [ ] Display confidence level: "HIGH", "MEDIUM", or "LOW"
- [ ] Optional: Color code (same as risk tier)
- [ ] Show missing biomarker count: e.g., "Missing: 0/11"
- [ ] Explain what this means:
  - HIGH (0 missing): Full biomarker data, reliable prediction
  - MEDIUM (1-2 missing): Some data gaps, reasonable prediction
  - LOW (3+ missing): Significant gaps, prediction may be unreliable

### ✅ Timestamp

- [ ] Display `generated_timestamp` in user's local timezone
- [ ] Convert from ISO 8601 UTC to readable format
- [ ] Example: "Generated on June 2, 2026 at 10:45 AM"
- [ ] Use `new Date(isoString).toLocaleString()`

### ✅ Complete Results Panel HTML Structure

```html
<div class="results-container">
  <!-- Probability & Risk Tier -->
  <div class="probability-card">
    <h3>Success Probability</h3>
    <div class="probability-value">72.0%</div>
    <div class="risk-tier" style="color: #2fd9ff; background: rgba(47, 217, 255, 0.1);">
      LOW Risk
    </div>
  </div>
  
  <!-- Top Drivers -->
  <div class="drivers-card">
    <h3>Top Model Drivers</h3>
    <div class="drivers-list">
      <div class="driver">1. trial sample size ↑ (coef: 1.422)</div>
      <div class="driver">2. age mean ↓ (coef: -0.845)</div>
      <!-- ... more drivers ... -->
    </div>
  </div>
  
  <!-- Biomarker Explanation -->
  <div class="explanation-card">
    <h3>Biomarker Analysis</h3>
    <p>This trial enrolls participants with...</p>
  </div>
  
  <!-- Confidence & Data Quality -->
  <div class="confidence-card">
    <h3>Data Quality</h3>
    <div class="confidence-badge">HIGH Confidence</div>
    <p>Missing biomarkers: 0 / 11</p>
    <p>Generated: June 2, 2026 at 10:45 AM</p>
  </div>
</div>
```

---

## SECTION 6: VALIDATION CHECKLIST

### ✅ Client-Side Form Validation (Before Sending)

- [ ] `trial_design.trial_sample_size` is integer > 0
- [ ] `trial_design.trial_duration_weeks` is integer > 0
- [ ] `endpoints.endpoint_type` is one of: objective, subjective, mixed
- [ ] `endpoints.primary_endpoint_name` is not empty string
- [ ] `enrollment.age_mean` is number > 0
- [ ] `baseline_mmse` (if provided) is between 0-30
- [ ] `baseline_moca` (if provided) is between 0-30
- [ ] `cdr_baseline` (if provided) is between 0-18
- [ ] Form not submitted while previous request is pending
- [ ] Display all validation errors at once

### ✅ Network Validation (During/After Send)

- [ ] Request sent as POST with correct URL
- [ ] Response status is 200 (not 400 or 500)
- [ ] Response body is valid JSON
- [ ] Response includes all required fields
- [ ] trial_success_probability is between 0-1
- [ ] risk_tier is one of: HIGH, MEDIUM, LOW
- [ ] confidence_flag is one of: HIGH, MEDIUM, LOW
- [ ] Timestamp can be parsed as valid ISO 8601

### ✅ Test Cases (Must Pass)

| Test Case | Input | Expected Result | Status |
|-----------|-------|-----------------|--------|
| Minimum fields | Only required 5 fields | 200 response, LOW confidence | ⏳ |
| All fields | All fields populated | 200 response, HIGH confidence | ⏳ |
| Missing sample_size | Omit trial_sample_size | Show validation error before send | ⏳ |
| Missing duration | Omit trial_duration_weeks | Show validation error before send | ⏳ |
| Missing endpoint_type | Omit endpoint_type | Show validation error before send | ⏳ |
| Missing endpoint_name | Omit primary_endpoint_name | Show validation error before send | ⏳ |
| Missing age_mean | Omit age_mean | Show validation error before send | ⏳ |
| Invalid endpoint_type | Send "invalid_type" | 400 error from API | ⏳ |
| Invalid MMSE | Send "40" (>30) | Show validation error before send | ⏳ |
| Network timeout | Simulate 60 sec delay | Show timeout error message | ⏳ |
| API offline | Stop backend server | Show "server unreachable" message | ⏳ |

---

## SECTION 7: RESPONSE PARSING CODE

### ✅ JavaScript Function: Parse & Validate Response

```javascript
/**
 * Validate API response matches expected schema
 * @param {Object} data - Response JSON from API
 * @returns {Object} - { isValid: boolean, errors: string[] }
 */
function validatePredictionResponse(data) {
  const errors = [];
  
  // Check required top-level fields
  if (typeof data.trial_success_probability !== 'number' ||
      data.trial_success_probability < 0 || 
      data.trial_success_probability > 1) {
    errors.push('Invalid trial_success_probability (must be 0-1)');
  }
  
  if (!['HIGH', 'MEDIUM', 'LOW'].includes(data.risk_tier)) {
    errors.push('Invalid risk_tier (must be HIGH, MEDIUM, or LOW)');
  }
  
  if (!Array.isArray(data.top_drivers)) {
    errors.push('top_drivers must be an array');
  } else {
    data.top_drivers.forEach((driver, idx) => {
      if (!driver.feature_name) errors.push(`Driver ${idx}: missing feature_name`);
      if (typeof driver.coefficient !== 'number') errors.push(`Driver ${idx}: invalid coefficient`);
      if (!['positive', 'negative'].includes(driver.direction)) errors.push(`Driver ${idx}: invalid direction`);
    });
  }
  
  if (typeof data.biomarker_explanation !== 'string' || !data.biomarker_explanation) {
    errors.push('Invalid biomarker_explanation');
  }
  
  if (!['HIGH', 'MEDIUM', 'LOW'].includes(data.confidence_flag)) {
    errors.push('Invalid confidence_flag');
  }
  
  if (typeof data.missing_biomarker_count !== 'number' || 
      data.missing_biomarker_count < 0 || 
      data.missing_biomarker_count > 11) {
    errors.push('Invalid missing_biomarker_count');
  }
  
  if (!data.generated_timestamp || isNaN(Date.parse(data.generated_timestamp))) {
    errors.push('Invalid timestamp');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

---

## SECTION 8: INTEGRATION WORKFLOW

### Step 1: Build Form HTML ✅
- [ ] Create form with all field names from spec
- [ ] Use correct input types (number, text, checkbox, select)
- [ ] Set required attribute on 5 critical fields
- [ ] Group fields into sections for clarity

### Step 2: Implement Form Validation ✅
- [ ] Write `validatePredictionForm(formElement)` function
- [ ] Check all 5 required fields
- [ ] Validate numeric ranges
- [ ] Return list of error messages
- [ ] Show errors to user before API call

### Step 3: Implement JSON Building ✅
- [ ] Write `buildPredictionRequest(formElement)` function
- [ ] Convert form data to nested JSON structure
- [ ] Type convert numbers correctly (int vs float)
- [ ] Omit empty/null values
- [ ] Validate structure matches spec

### Step 4: Implement API Call ✅
- [ ] Write `sendPredictionRequest(requestJSON)` function
- [ ] Use fetch() with POST, correct headers, 30s timeout
- [ ] Check response.ok before parsing
- [ ] Return parsed JSON or throw error
- [ ] Handle network errors gracefully

### Step 5: Implement Results Display ✅
- [ ] Write `displayPredictionResults(response)` function
- [ ] Validate response structure
- [ ] Format probability as percentage
- [ ] Color-code risk tier
- [ ] Display drivers, explanation, confidence
- [ ] Show in readable layout

### Step 6: Implement Error Handling ✅
- [ ] Write error display function
- [ ] Handle validation errors
- [ ] Handle 400 Bad Request errors
- [ ] Handle 500 Server errors
- [ ] Handle network errors
- [ ] Keep form data when showing errors

### Step 7: Form Submission ✅
- [ ] Create `handlePredictionFormSubmit(event)` function
- [ ] Call validate() → build() → send() → display()
- [ ] Disable submit button during request
- [ ] Show loading indicator
- [ ] Handle errors throughout chain

### Step 8: Testing ✅
- [ ] Test with minimum required fields
- [ ] Test with complete data
- [ ] Test validation errors
- [ ] Test invalid enum values
- [ ] Test network timeout
- [ ] Test API offline scenario

---

## SECTION 9: SUMMARY

### What the Frontend Must Do

1. **Collect User Input**
   - Trial design: sample size, duration
   - Endpoints: type, primary measure
   - Enrollment: mean age (+ optional MMSE, MoCA, CDR)
   - Biomarkers: optional checklist/text inputs
   - Enrichment strategy: optional dropdown

2. **Validate Locally**
   - 5 required fields must be present
   - Numbers must be valid ranges
   - Endpoint type must be one of three values
   - Show errors before API call

3. **Build JSON**
   - Nested structure with 4 sections
   - Type conversions (int/float/string)
   - Omit empty values
   - Match field names exactly

4. **Send to API**
   - POST to http://127.0.0.1:8000/predict
   - Include Content-Type: application/json header
   - 30-second timeout
   - Handle network errors

5. **Display Results**
   - Probability as percentage
   - Risk tier with color
   - Top 5 drivers
   - Biomarker explanation text
   - Confidence flag and missing count

6. **Handle Errors**
   - Show validation errors before submit
   - Show server errors from API (400/500)
   - Show network errors
   - Keep form data for retry

### What the Backend Will Do

✅ Validate required fields (already done)  
✅ Engineer 29 features from 22 inputs (already done)  
✅ Load logistic regression model (already done)  
✅ Return probability + drivers + explanation (already done)  

### Success Criteria

- [ ] Form accepts all required fields
- [ ] Form validates locally before submit
- [ ] Request JSON matches specification
- [ ] API returns 200 status
- [ ] Response parsed and displayed correctly
- [ ] Errors handled gracefully
- [ ] All test cases pass
- [ ] User can make multiple predictions

---

**Audit & Specification Complete**  
**Ready for Frontend Implementation**  
**Date: June 2, 2026**
