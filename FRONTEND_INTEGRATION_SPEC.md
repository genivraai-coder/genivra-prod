# 🎨 FRONTEND INTEGRATION SPECIFICATION - GENIVRA API

**Date:** June 2, 2026  
**Purpose:** Exact field mappings, JSON payload examples, and integration code snippets  
**Target:** Frontend developer rebuilding genivra_final.html

---

## 1. REQUIRED FORM FIELDS & FIELD NAMES

### Important: Field names MUST EXACTLY MATCH backend schema

Use these exact field names in your HTML form `<input>` elements:

```html
<!-- TRIAL DESIGN -->
<input name="trial_design.trial_sample_size" type="number" min="1" required />
<input name="trial_design.trial_duration_weeks" type="number" min="1" required />
<input name="trial_design.number_of_arms" type="number" min="1" />
<input name="trial_design.randomization_ratio" type="text" />
<input name="trial_design.phase" type="text" />
<input name="trial_design.indication" type="text" />

<!-- ENDPOINTS -->
<select name="endpoint_type" required>
  <option value="">Select...</option>
  <option value="objective">Objective</option>
  <option value="subjective">Subjective</option>
  <option value="mixed">Mixed</option>
</select>
<input name="primary_endpoint_name" type="text" required placeholder="e.g., CDR-SB, ADAS-Cog, MMSE" />

<!-- BIOMARKERS (All optional) -->
<input name="apoe_e4_carrier" type="checkbox" value="1" />
<input name="apoe_e4_homozygous" type="checkbox" value="1" />
<input name="ptau217_high" type="checkbox" value="1" />
<input name="ptau217_continuous" type="number" step="0.01" />
<input name="csf_abeta42_40_ratio_low" type="checkbox" value="1" />
<input name="csf_abeta42_40_ratio_continuous" type="number" step="0.01" />
<input name="csf_ptau_elevated" type="checkbox" value="1" />
<input name="amyloid_pet_positive" type="checkbox" value="1" />
<input name="tau_pet_positive" type="checkbox" value="1" />
<input name="hippocampal_atrophy_mri" type="number" step="0.1" />
<input name="hippocampal_atrophy_binary" type="checkbox" value="1" />

<!-- ENROLLMENT -->
<input name="age_mean" type="number" step="0.1" required />
<input name="baseline_mmse" type="number" min="0" max="30" step="0.1" />
<input name="baseline_moca" type="number" min="0" max="30" step="0.1" />
<input name="cdr_baseline" type="number" min="0" max="18" step="0.1" />

<!-- ENRICHMENT STRATEGY -->
<select name="biomarker_enrichment_strategy">
  <option value="">Select...</option>
  <option value="amyloid_positive">Amyloid Positive</option>
  <option value="tau_positive">Tau Positive</option>
  <option value="at_positive">A/T Positive</option>
  <option value="cognitive_only">Cognitive Only</option>
  <option value="none">None</option>
</select>

<!-- TOP-LEVEL (Optional) -->
<input name="phase" type="text" />
<input name="indication" type="text" />
```

---

## 2. FORM DATA → JSON CONVERSION LOGIC

### JavaScript Function: `buildPredictionRequest(formElement)`

```javascript
/**
 * Convert form data to PredictionRequest JSON
 * @param {HTMLFormElement} formElement - The form to read
 * @returns {Object} - PredictionRequest JSON object
 */
function buildPredictionRequest(formElement) {
  const formData = new FormData(formElement);
  
  // Initialize nested objects
  const request = {
    trial_design: {},
    endpoints: {},
    biomarkers: {},
    enrollment: {}
  };
  
  // Top-level optional fields
  const topLevelFields = ['phase', 'indication', 'biomarker_enrichment_strategy'];
  
  // Iterate through form fields
  for (const [key, value] of formData.entries()) {
    // Skip empty values
    if (value === '' || value === null) {
      continue;
    }
    
    // Handle nested fields (e.g., "trial_design.trial_sample_size")
    if (key.includes('.')) {
      const [section, fieldName] = key.split('.');
      
      // Type conversion
      let typedValue = value;
      
      // Integer fields
      if (['trial_sample_size', 'trial_duration_weeks', 'number_of_arms', 
           'apoe_e4_carrier', 'apoe_e4_homozygous', 'ptau217_high',
           'csf_abeta42_40_ratio_low', 'csf_ptau_elevated', 'amyloid_pet_positive',
           'tau_pet_positive', 'hippocampal_atrophy_binary'].includes(fieldName)) {
        typedValue = parseInt(value, 10);
      }
      // Float fields
      else if (['ptau217_continuous', 'csf_abeta42_40_ratio_continuous', 
                'hippocampal_atrophy_mri', 'age_mean', 'baseline_mmse', 
                'baseline_moca', 'cdr_baseline'].includes(fieldName)) {
        typedValue = parseFloat(value);
      }
      
      request[section][fieldName] = typedValue;
    }
    // Handle top-level fields
    else if (topLevelFields.includes(key)) {
      if (key === 'biomarker_enrichment_strategy' && value) {
        request[key] = value;
      } else if (key !== 'biomarker_enrichment_strategy') {
        request[key] = value;
      }
    }
  }
  
  return request;
}
```

---

## 3. FIELD MAPPING TABLE: HTML ↔ JSON

| HTML Input Name | JSON Path | Type | Required | Example |
|---|---|---|---|---|
| `trial_design.trial_sample_size` | `request.trial_design.trial_sample_size` | int | ✅ | `200` |
| `trial_design.trial_duration_weeks` | `request.trial_design.trial_duration_weeks` | int | ✅ | `52` |
| `trial_design.number_of_arms` | `request.trial_design.number_of_arms` | int | ❌ | `2` |
| `trial_design.randomization_ratio` | `request.trial_design.randomization_ratio` | str | ❌ | `"1:1"` |
| `trial_design.phase` | `request.trial_design.phase` | str | ❌ | `"Phase II"` |
| `trial_design.indication` | `request.trial_design.indication` | str | ❌ | `"Alzheimer's Disease"` |
| `endpoint_type` | `request.endpoints.endpoint_type` | str | ✅ | `"objective"` |
| `primary_endpoint_name` | `request.endpoints.primary_endpoint_name` | str | ✅ | `"CDR-SB"` |
| `apoe_e4_carrier` | `request.biomarkers.apoe_e4_carrier` | int (0/1) | ❌ | `1` |
| `apoe_e4_homozygous` | `request.biomarkers.apoe_e4_homozygous` | int (0/1) | ❌ | `0` |
| `ptau217_high` | `request.biomarkers.ptau217_high` | int (0/1) | ❌ | `1` |
| `ptau217_continuous` | `request.biomarkers.ptau217_continuous` | float | ❌ | `18.5` |
| `csf_abeta42_40_ratio_low` | `request.biomarkers.csf_abeta42_40_ratio_low` | int (0/1) | ❌ | `1` |
| `csf_abeta42_40_ratio_continuous` | `request.biomarkers.csf_abeta42_40_ratio_continuous` | float | ❌ | `0.45` |
| `csf_ptau_elevated` | `request.biomarkers.csf_ptau_elevated` | int (0/1) | ❌ | `1` |
| `amyloid_pet_positive` | `request.biomarkers.amyloid_pet_positive` | int (0/1) | ❌ | `1` |
| `tau_pet_positive` | `request.biomarkers.tau_pet_positive` | int (0/1) | ❌ | `0` |
| `hippocampal_atrophy_mri` | `request.biomarkers.hippocampal_atrophy_mri` | float | ❌ | `3200.0` |
| `hippocampal_atrophy_binary` | `request.biomarkers.hippocampal_atrophy_binary` | int (0/1) | ❌ | `1` |
| `age_mean` | `request.enrollment.age_mean` | float | ✅ | `72.5` |
| `baseline_mmse` | `request.enrollment.baseline_mmse` | float | ❌ | `22.0` |
| `baseline_moca` | `request.enrollment.baseline_moca` | float | ❌ | `19.0` |
| `cdr_baseline` | `request.enrollment.cdr_baseline` | float | ❌ | `1.5` |
| `biomarker_enrichment_strategy` | `request.biomarker_enrichment_strategy` | str | ❌ | `"at_positive"` |
| `phase` | `request.phase` | str | ❌ | `"Phase II"` |
| `indication` | `request.indication` | str | ❌ | `"Alzheimer's Disease"` |

---

## 4. EXAMPLE VALID REQUEST/RESPONSE PAYLOADS

### Minimal Request (MVP - only required fields)

```json
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
```

**Expected Response:**
```json
{
  "trial_success_probability": 0.58,
  "risk_tier": "MEDIUM",
  "top_drivers": [
    {
      "feature_name": "trial_sample_size",
      "coefficient": 1.422,
      "direction": "positive",
      "impact_magnitude": 1.422
    },
    {
      "feature_name": "age_mean",
      "coefficient": -0.845,
      "direction": "negative",
      "impact_magnitude": 0.845
    }
  ],
  "biomarker_explanation": "Trial enrolls average-aged participants (72.5 years) with modest sample size (200). Limited biomarker data available. Model predicts moderate success probability, indicating uncertain outcome.",
  "confidence_flag": "LOW",
  "missing_biomarker_count": 10,
  "model_version": "v1.0",
  "generated_timestamp": "2026-06-02T10:45:30.123456Z"
}
```

---

### Complete Request (All fields, HIGH confidence)

```json
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
    "ptau217_continuous": 18.5,
    "csf_abeta42_40_ratio_low": 1,
    "csf_abeta42_40_ratio_continuous": 0.45,
    "csf_ptau_elevated": 0,
    "amyloid_pet_positive": 1,
    "tau_pet_positive": 0,
    "hippocampal_atrophy_mri": 3200.0,
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

**Expected Response:**
```json
{
  "trial_success_probability": 0.72,
  "risk_tier": "LOW",
  "top_drivers": [
    {
      "feature_name": "trial_sample_size",
      "coefficient": 1.422,
      "direction": "positive",
      "impact_magnitude": 1.422
    },
    {
      "feature_name": "age_mean",
      "coefficient": -0.845,
      "direction": "negative",
      "impact_magnitude": 0.845
    },
    {
      "feature_name": "amyloid_pet_positive",
      "coefficient": 0.934,
      "direction": "positive",
      "impact_magnitude": 0.934
    },
    {
      "feature_name": "endpoint_type_objective",
      "coefficient": 0.567,
      "direction": "positive",
      "impact_magnitude": 0.567
    },
    {
      "feature_name": "baseline_mmse",
      "coefficient": 0.123,
      "direction": "positive",
      "impact_magnitude": 0.123
    }
  ],
  "biomarker_explanation": "This trial enrolls participants with amyloid PET positive and elevated plasma p-tau217 biomarker profile. Enrichment strategy is 'at_positive', targeting specific biomarker populations. Trial design includes adequate sample size and extended follow-up duration. Model predicts 72% success probability, indicating strong evidence for success. Primary model drivers: trial_sample_size (increases success) and amyloid_pet_positive (increases success).",
  "confidence_flag": "HIGH",
  "missing_biomarker_count": 0,
  "model_version": "v1.0",
  "generated_timestamp": "2026-06-02T10:45:30.456789Z"
}
```

---

### Error Response (Missing Required Field)

```json
{
  "error": "validation error",
  "message": "Missing required field: trial_sample_size",
  "status_code": 400,
  "timestamp": "2026-06-02T10:45:30Z"
}
```

---

## 5. API CALL JAVASCRIPT CODE

### Function: `sendPredictionRequest(requestJSON)`

```javascript
/**
 * Send prediction request to backend API
 * @param {Object} requestJSON - PredictionRequest object
 * @returns {Promise<Object>} - PredictionResponse or error
 */
async function sendPredictionRequest(requestJSON) {
  const apiUrl = 'http://127.0.0.1:8000/predict';
  
  try {
    // Show loading indicator
    showLoadingSpinner();
    
    // Send POST request
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Optional: Add API key if in production
        // 'x-api-key': apiKey
      },
      body: JSON.stringify(requestJSON),
      timeout: 30000 // 30 second timeout
    });
    
    // Hide loading
    hideLoadingSpinner();
    
    // Handle non-200 responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.message || 
        `API returned ${response.status}: ${response.statusText}`
      );
    }
    
    // Parse successful response
    const data = await response.json();
    return data;
    
  } catch (error) {
    hideLoadingSpinner();
    
    // Handle different error types
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      throw new Error('API server unreachable. Ensure backend is running on localhost:8000');
    } else if (error.message.includes('timeout')) {
      throw new Error('Request timed out. API server may be slow or unreachable.');
    } else {
      throw error;
    }
  }
}
```

---

## 6. FORM VALIDATION JAVASCRIPT CODE

### Function: `validatePredictionForm(formElement)`

```javascript
/**
 * Validate form before submission
 * @param {HTMLFormElement} formElement - Form to validate
 * @returns {Object} - { isValid: boolean, errors: string[] }
 */
function validatePredictionForm(formElement) {
  const errors = [];
  
  // Helper to get field value
  const getFieldValue = (name) => {
    const input = formElement.querySelector(`[name="${name}"]`);
    return input ? input.value : '';
  };
  
  // Check required fields
  const trialSampleSize = getFieldValue('trial_design.trial_sample_size');
  if (!trialSampleSize || parseInt(trialSampleSize) <= 0) {
    errors.push('Trial Sample Size is required and must be greater than 0');
  }
  
  const trialDuration = getFieldValue('trial_design.trial_duration_weeks');
  if (!trialDuration || parseInt(trialDuration) <= 0) {
    errors.push('Trial Duration (weeks) is required and must be greater than 0');
  }
  
  const endpointType = getFieldValue('endpoint_type');
  if (!endpointType) {
    errors.push('Endpoint Type is required');
  } else if (!['objective', 'subjective', 'mixed'].includes(endpointType)) {
    errors.push('Invalid Endpoint Type. Must be: objective, subjective, or mixed');
  }
  
  const primaryEndpoint = getFieldValue('primary_endpoint_name');
  if (!primaryEndpoint) {
    errors.push('Primary Endpoint Name is required');
  }
  
  const ageMean = getFieldValue('age_mean');
  if (!ageMean || parseFloat(ageMean) <= 0) {
    errors.push('Mean Age is required and must be greater than 0');
  }
  
  // Validate numeric ranges
  const baselineMmse = getFieldValue('baseline_mmse');
  if (baselineMmse && (parseFloat(baselineMmse) < 0 || parseFloat(baselineMmse) > 30)) {
    errors.push('Baseline MMSE must be between 0 and 30');
  }
  
  const baselineMoca = getFieldValue('baseline_moca');
  if (baselineMoca && (parseFloat(baselineMoca) < 0 || parseFloat(baselineMoca) > 30)) {
    errors.push('Baseline MoCA must be between 0 and 30');
  }
  
  const cdrBaseline = getFieldValue('cdr_baseline');
  if (cdrBaseline && (parseFloat(cdrBaseline) < 0 || parseFloat(cdrBaseline) > 18)) {
    errors.push('CDR Baseline must be between 0 and 18');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

---

## 7. RESULT DISPLAY JAVASCRIPT CODE

### Function: `displayPredictionResults(response)`

```javascript
/**
 * Display prediction results on page
 * @param {Object} response - PredictionResponse from API
 */
function displayPredictionResults(response) {
  // Get result container
  const resultsDiv = document.getElementById('prediction-results');
  
  // Format probability as percentage
  const probabilityPercent = (response.trial_success_probability * 100).toFixed(1);
  
  // Color code based on risk tier
  let tierColor, tierBgColor;
  switch(response.risk_tier) {
    case 'LOW':
      tierColor = '#2fd9ff'; // Neon cyan
      tierBgColor = 'rgba(47, 217, 255, 0.1)';
      break;
    case 'MEDIUM':
      tierColor = '#ffa500'; // Orange
      tierBgColor = 'rgba(255, 165, 0, 0.1)';
      break;
    case 'HIGH':
      tierColor = '#ff6b6b'; // Red
      tierBgColor = 'rgba(255, 107, 107, 0.1)';
      break;
  }
  
  // Build top drivers HTML
  let driversHTML = '';
  if (response.top_drivers && response.top_drivers.length > 0) {
    driversHTML = '<div class="top-drivers">';
    response.top_drivers.forEach((driver, index) => {
      const directionIcon = driver.direction === 'positive' ? '↑' : '↓';
      driversHTML += `
        <div class="driver-item">
          <span class="rank">${index + 1}</span>
          <span class="name">${driver.feature_name.replace(/_/g, ' ')}</span>
          <span class="direction ${driver.direction}">${directionIcon}</span>
          <span class="coefficient">${driver.coefficient.toFixed(3)}</span>
        </div>
      `;
    });
    driversHTML += '</div>';
  }
  
  // Build confidence badge
  let confidenceColor;
  switch(response.confidence_flag) {
    case 'HIGH':
      confidenceColor = '#2fd9ff';
      break;
    case 'MEDIUM':
      confidenceColor = '#ffa500';
      break;
    case 'LOW':
      confidenceColor = '#ff6b6b';
      break;
  }
  
  // Build complete HTML
  const html = `
    <div class="results-container">
      <div class="probability-card" style="border-left: 4px solid ${tierColor};">
        <h3>Success Probability</h3>
        <div class="probability-value">${probabilityPercent}%</div>
        <div class="risk-tier" style="background: ${tierBgColor}; color: ${tierColor};">
          ${response.risk_tier} Risk
        </div>
      </div>
      
      <div class="explanation-card">
        <h3>Biomarker Explanation</h3>
        <p>${response.biomarker_explanation}</p>
      </div>
      
      <div class="drivers-card">
        <h3>Top Drivers</h3>
        ${driversHTML}
      </div>
      
      <div class="confidence-card">
        <h3>Data Quality</h3>
        <div class="confidence-badge" style="color: ${confidenceColor};">
          ${response.confidence_flag} Confidence
        </div>
        <p>Missing biomarkers: ${response.missing_biomarker_count} / 11</p>
        <p>Timestamp: ${new Date(response.generated_timestamp).toLocaleString()}</p>
      </div>
    </div>
  `;
  
  resultsDiv.innerHTML = html;
  resultsDiv.style.display = 'block';
  
  // Scroll to results
  resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
```

---

## 8. COMPLETE FORM SUBMIT HANDLER

### Function: `handlePredictionFormSubmit(event)`

```javascript
/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
async function handlePredictionFormSubmit(event) {
  event.preventDefault();
  
  const form = event.target;
  const resultsDiv = document.getElementById('prediction-results');
  const errorDiv = document.getElementById('error-message');
  
  // Clear previous results/errors
  resultsDiv.style.display = 'none';
  errorDiv.style.display = 'none';
  
  try {
    // Step 1: Validate form
    const validation = validatePredictionForm(form);
    if (!validation.isValid) {
      showError(validation.errors.join('\n'));
      return;
    }
    
    // Step 2: Build JSON request
    const requestJSON = buildPredictionRequest(form);
    console.log('Sending request:', requestJSON);
    
    // Step 3: Send to API
    const response = await sendPredictionRequest(requestJSON);
    console.log('Received response:', response);
    
    // Step 4: Display results
    displayPredictionResults(response);
    
  } catch (error) {
    console.error('Error:', error);
    showError(error.message);
  }
}

/**
 * Show error message to user
 * @param {string} message - Error message(s)
 */
function showError(message) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.innerHTML = `<div class="error-alert">${message.replace(/\n/g, '<br>')}</div>`;
  errorDiv.style.display = 'block';
  errorDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Show loading spinner
 */
function showLoadingSpinner() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) {
    spinner.style.display = 'flex';
  }
}

/**
 * Hide loading spinner
 */
function hideLoadingSpinner() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) {
    spinner.style.display = 'none';
  }
}
```

---

## 9. HTML STRUCTURE TEMPLATE

### Complete form HTML structure (recommended)

```html
<div class="prediction-container">
  <!-- Error messages -->
  <div id="error-message" style="display: none;"></div>
  
  <!-- Loading spinner -->
  <div id="loading-spinner" class="loading-spinner" style="display: none;">
    <div class="spinner"></div>
    <p>Making prediction...</p>
  </div>
  
  <!-- Prediction form -->
  <form id="prediction-form" onsubmit="handlePredictionFormSubmit(event)">
    
    <!-- TRIAL DESIGN SECTION -->
    <fieldset class="form-section">
      <legend>Trial Design</legend>
      
      <div class="form-group">
        <label for="trial_sample_size">Sample Size *</label>
        <input id="trial_sample_size" name="trial_design.trial_sample_size" 
               type="number" min="1" required placeholder="e.g., 200" />
      </div>
      
      <div class="form-group">
        <label for="trial_duration">Duration (weeks) *</label>
        <input id="trial_duration" name="trial_design.trial_duration_weeks" 
               type="number" min="1" required placeholder="e.g., 52" />
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="number_of_arms">Number of Arms</label>
          <input id="number_of_arms" name="trial_design.number_of_arms" 
                 type="number" min="1" placeholder="e.g., 2" />
        </div>
        
        <div class="form-group">
          <label for="randomization">Randomization Ratio</label>
          <input id="randomization" name="trial_design.randomization_ratio" 
                 type="text" placeholder="e.g., 1:1" />
        </div>
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="phase">Phase</label>
          <input id="phase" name="trial_design.phase" 
                 type="text" placeholder="e.g., Phase II" />
        </div>
        
        <div class="form-group">
          <label for="indication">Indication</label>
          <input id="indication" name="trial_design.indication" 
                 type="text" placeholder="e.g., Alzheimer's Disease" />
        </div>
      </div>
    </fieldset>
    
    <!-- ENDPOINTS SECTION -->
    <fieldset class="form-section">
      <legend>Endpoints</legend>
      
      <div class="form-group">
        <label for="endpoint_type">Endpoint Type *</label>
        <select id="endpoint_type" name="endpoint_type" required>
          <option value="">Select...</option>
          <option value="objective">Objective</option>
          <option value="subjective">Subjective</option>
          <option value="mixed">Mixed</option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="primary_endpoint">Primary Endpoint *</label>
        <input id="primary_endpoint" name="primary_endpoint_name" 
               type="text" required placeholder="e.g., CDR-SB" />
      </div>
    </fieldset>
    
    <!-- ENROLLMENT SECTION -->
    <fieldset class="form-section">
      <legend>Enrollment</legend>
      
      <div class="form-group">
        <label for="age_mean">Mean Age (years) *</label>
        <input id="age_mean" name="age_mean" 
               type="number" step="0.1" required placeholder="e.g., 72.5" />
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="baseline_mmse">Baseline MMSE (0-30)</label>
          <input id="baseline_mmse" name="baseline_mmse" 
                 type="number" min="0" max="30" step="0.1" placeholder="e.g., 22" />
        </div>
        
        <div class="form-group">
          <label for="baseline_moca">Baseline MoCA (0-30)</label>
          <input id="baseline_moca" name="baseline_moca" 
                 type="number" min="0" max="30" step="0.1" placeholder="e.g., 19" />
        </div>
        
        <div class="form-group">
          <label for="cdr_baseline">CDR Baseline (0-18)</label>
          <input id="cdr_baseline" name="cdr_baseline" 
                 type="number" min="0" max="18" step="0.1" placeholder="e.g., 1.5" />
        </div>
      </div>
    </fieldset>
    
    <!-- BIOMARKERS SECTION -->
    <fieldset class="form-section">
      <legend>Biomarkers (Optional)</legend>
      
      <div class="biomarker-group">
        <h4>Genetic / Plasma</h4>
        <div class="checkbox-grid">
          <label>
            <input name="apoe_e4_carrier" type="checkbox" value="1" />
            APOE ε4 Carrier
          </label>
          <label>
            <input name="apoe_e4_homozygous" type="checkbox" value="1" />
            APOE ε4 Homozygous
          </label>
          <label>
            <input name="ptau217_high" type="checkbox" value="1" />
            p-tau217 High
          </label>
        </div>
        
        <label class="input-label">
          p-tau217 Continuous (pg/mL)
          <input name="ptau217_continuous" type="number" step="0.01" />
        </label>
      </div>
      
      <div class="biomarker-group">
        <h4>CSF</h4>
        <div class="checkbox-grid">
          <label>
            <input name="csf_abeta42_40_ratio_low" type="checkbox" value="1" />
            Aβ42/40 Ratio Low
          </label>
          <label>
            <input name="csf_ptau_elevated" type="checkbox" value="1" />
            p-tau Elevated
          </label>
        </div>
        
        <label class="input-label">
          Aβ42/40 Ratio Continuous
          <input name="csf_abeta42_40_ratio_continuous" type="number" step="0.01" />
        </label>
      </div>
      
      <div class="biomarker-group">
        <h4>PET Imaging</h4>
        <div class="checkbox-grid">
          <label>
            <input name="amyloid_pet_positive" type="checkbox" value="1" />
            Amyloid PET Positive
          </label>
          <label>
            <input name="tau_pet_positive" type="checkbox" value="1" />
            Tau PET Positive
          </label>
        </div>
      </div>
      
      <div class="biomarker-group">
        <h4>MRI</h4>
        <div class="checkbox-grid">
          <label>
            <input name="hippocampal_atrophy_binary" type="checkbox" value="1" />
            Hippocampal Atrophy
          </label>
        </div>
        
        <label class="input-label">
          Hippocampal Volume (mm³)
          <input name="hippocampal_atrophy_mri" type="number" step="0.1" />
        </label>
      </div>
    </fieldset>
    
    <!-- ENRICHMENT STRATEGY -->
    <fieldset class="form-section">
      <legend>Enrichment Strategy</legend>
      
      <div class="form-group">
        <label for="enrichment">Biomarker Enrichment Strategy</label>
        <select id="enrichment" name="biomarker_enrichment_strategy">
          <option value="">Select...</option>
          <option value="amyloid_positive">Amyloid Positive</option>
          <option value="tau_positive">Tau Positive</option>
          <option value="at_positive">A/T Positive</option>
          <option value="cognitive_only">Cognitive Only</option>
          <option value="none">None</option>
        </select>
      </div>
    </fieldset>
    
    <!-- SUBMIT BUTTON -->
    <div class="form-actions">
      <button type="submit" class="btn-primary">
        Get Prediction
      </button>
      <button type="reset" class="btn-secondary">
        Clear Form
      </button>
    </div>
  </form>
  
  <!-- RESULTS DISPLAY -->
  <div id="prediction-results" style="display: none;"></div>
</div>
```

---

## 10. CHECKLIST FOR FRONTEND DEVELOPER

### Pre-Integration
- [ ] Form HTML created with all required fields
- [ ] Form input names exactly match specification above
- [ ] JavaScript functions imported/loaded before form use

### Form Validation
- [ ] `validatePredictionForm()` function implemented
- [ ] Validates all 5 required fields
- [ ] Shows error messages for invalid inputs
- [ ] Prevents submission with incomplete data

### JSON Building
- [ ] `buildPredictionRequest()` function converts form → JSON
- [ ] Correctly maps HTML input names to JSON paths
- [ ] Converts string values to int/float as needed
- [ ] Omits empty/null values
- [ ] Generates valid PredictionRequest matching spec

### API Communication
- [ ] `sendPredictionRequest()` sends POST to http://127.0.0.1:8000/predict
- [ ] Includes Content-Type: application/json header
- [ ] Handles 200 responses as success
- [ ] Handles 400/500 responses as errors
- [ ] 30-second timeout implemented
- [ ] Shows meaningful error messages

### Results Display
- [ ] `displayPredictionResults()` renders response
- [ ] Shows success probability as percentage
- [ ] Color-codes risk tier (GREEN=LOW, YELLOW=MEDIUM, RED=HIGH)
- [ ] Lists top 5 drivers with names and coefficients
- [ ] Displays biomarker explanation text
- [ ] Shows confidence flag and missing biomarker count

### Testing
- [ ] Test with minimum required fields
- [ ] Test with all fields populated
- [ ] Test with invalid required field (should show error)
- [ ] Test with invalid data type (should show error)
- [ ] Test with network timeout (should show meaningful error)
- [ ] Verify results match expected probability/tier

---

**Integration Guide Completed:** June 2, 2026  
**Status:** Ready for Frontend Implementation ✅
