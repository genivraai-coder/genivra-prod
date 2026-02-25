# ML Scope: Alzheimer's Disease Phase II Trial Success Prediction

**Document Version:** 1.0  
**Last Updated:** February 20, 2026  
**Status:** Active Development

---

## 1. Objective

Build a machine learning model to **predict the probability that a Phase II Alzheimer's Disease trial advances to Phase III** or meets its primary endpoint.

### Key Metrics
- **Indication:** Alzheimer's Disease (AD)
- **Trial Phase:** Phase II
- **Target Event:** Trial advancement to Phase III OR primary endpoint success
- **Model Type:** Binary classification (success vs. failure)
- **Output:** Structured risk score with explainability

---

## 2. Success Label Definition

### Binary Classification
| Label | Definition | Examples |
|-------|-----------|----------|
| **1** | Trial Success | Trial advances to Phase III; Primary endpoint met (e.g., CDR-SB slowing ≥35%); Regulatory approval pathway clear |
| **0** | Trial Failure | Trial terminated early; Primary endpoint not met; Significant safety issues (ARIA); Lack of efficacy signals |

### Data Requirements
- Trial outcome status (from clinical trial database, ClinicalTrials.gov, or trial summary reports)
- Phase transition documentation (from regulatory filings or company press releases)
- Primary endpoint achievement metric (CDR-SB, ADAS-Cog, or trial-specific measure)

---

## 3. Output Requirements

Every trial scoring prediction must return a **structured JSON output** with the following fields:

```json
{
  "trial_id": "NCT_or_internal_id",
  "trial_name": "Study Name",
  "indication": "Alzheimer's Disease",
  "trial_phase": "Phase II",
  
  "trial_success_probability": 0.72,
  
  "risk_tier": "LOW",
  
  "top_5_feature_importance": [
    {
      "rank": 1,
      "feature": "APOE ε4 Homozygous Status",
      "importance_score": 0.35,
      "direction": "increases_risk"
    },
    {
      "rank": 2,
      "feature": "Plasma p-tau217 High",
      "importance_score": 0.28,
      "direction": "increases_risk"
    },
    {
      "rank": 3,
      "feature": "Amyloid PET Positive",
      "importance_score": 0.22,
      "direction": "increases_risk"
    },
    {
      "rank": 4,
      "feature": "Trial Duration (months)",
      "importance_score": 0.10,
      "direction": "decreases_risk"
    },
    {
      "rank": 5,
      "feature": "Enrollment Size",
      "importance_score": 0.05,
      "direction": "increases_risk"
    }
  ],
  
  "biomarker_explanation": "This trial enrolls early symptomatic Alzheimer's patients with elevated APOE ε4 carriers and positive amyloid PET. High plasma p-tau217 levels indicate active tau pathology (Nat Med 2025), supporting enrichment strategy. Biomarker profile aligns with NIA-AA AT(N) framework and predicts higher baseline cognitive decline risk. Model predicts 72% success probability based on similar past trials (lecanemab Phase II n=234, met primary endpoint CDR-SB -35% vs. placebo -10%). Risk is LOW due to strong biomarker evidence and adequate sample size.",
  
  "confidence_flag": "HIGH",
  
  "data_completeness": {
    "biomarker_data_provided": ["APOE", "Plasma_p_tau217", "Amyloid_PET"],
    "biomarker_data_missing": ["CSF_Aβ42", "Tau_PET"],
    "trial_design_data_provided": ["Phase", "Enrollment", "Duration", "Endpoint"],
    "completeness_percentage": 0.85
  },
  
  "model_version": "v1.0",
  "generated_timestamp": "2026-02-20T14:32:00Z"
}
```

### Field Definitions

**trial_success_probability** (float, 0–1)
- Model's predicted probability of trial success
- Derived from model's final classification layer (logistic/sigmoid output)

**risk_tier** (string: "LOW" | "MEDIUM" | "HIGH")
- Categorized risk based on success probability:
  - **LOW:** success_probability ≥ 0.70 (trials likely to advance)
  - **MEDIUM:** 0.40 ≤ success_probability < 0.70 (uncertain outcomes)
  - **HIGH:** success_probability < 0.40 (trials likely to fail)

**top_5_feature_importance** (array of objects)
- Ranked list of model's most influential input features
- Each includes:
  - **rank:** Position (1–5)
  - **feature:** Human-readable feature name
  - **importance_score:** Contribution magnitude (0–1, sums to ~1.0 across top 5)
  - **direction:** "increases_risk" or "decreases_risk" (effect interpretation)

**biomarker_explanation** (plain English narrative)
- Non-technical summary of:
  - Which biomarkers were present/absent in this trial
  - How those biomarkers relate to AD pathology (cite relevant framework: NIA-AA, published literature)
  - Comparison to historical successful trials
  - Overall risk assessment rationale
- Target audience: CNS fund managers, biotech BD teams, clinical decision-makers

**confidence_flag** (string: "HIGH" | "MEDIUM" | "LOW")
- Reflects data quality and model certainty:
  - **HIGH:** ≥80% biomarker data completeness, trial has design similarity to training set
  - **MEDIUM:** 50–79% completeness, some missing modalities (e.g., no tau PET)
  - **LOW:** <50% completeness, trial is outlier to training distribution

**data_completeness** (object)
- Lists which biomarkers were provided vs. missing
- Provides overall completeness % to explain confidence flag

---

## 4. Input Feature Specification

The ML model accepts a **structured trial descriptor** with the following feature groups:

### Group A: Biomarker Features (from Genivra Biomarker Logic Sheets)

#### Genetic
- `apoe_e4_status` (categorical: "homozygous" | "heterozygous" | "non_carrier" | "unknown")

#### Blood / Plasma
- `plasma_p_tau217_level` (continuous, pg/mL or n/a if missing)
- `plasma_p_tau217_high` (binary: 1 if elevated per assay threshold, 0 otherwise)
- `plasma_aβ42_aβ40_ratio` (continuous ratio or 0 if missing)
- `plasma_pct_aβ42_decreased` (binary: 1 if ≤0.5 ratio, 0 otherwise)

#### CSF (Lumbar Puncture)
- `csf_aβ42_level` (continuous, pg/mL or n/a)
- `csf_aβ42_decreased` (binary: 1 if <500 pg/mL, 0 otherwise)
- `csf_p_tau_level` (continuous or n/a)

#### Imaging
- `amyloid_pet_positive` (binary: 1 if SUVR >1.2, 0 if negative, 0.5 if borderline)
- `tau_pet_present` (binary: 1 if available and positive, 0 otherwise)
- `mri_hippocampal_atrophy_mm3` (continuous volume or 0 if not measured)

### Group B: Trial Design Features

- `trial_phase` (string: "Phase II" in v1)
- `enrollment_target_n` (integer: planned sample size)
- `trial_duration_months` (integer: planned duration)
- `randomization_ratio` (categorical: "1:1" | "2:1" | "open_label)
- `endpoint_type` (categorical: "objective" | "subjective" | "mixed")
- `primary_endpoint` (string: "CDR-SB" | "ADAS-Cog" | "MMSE" | "other")
- `endpoint_responder_threshold` (float: e.g., 35% decline slowing for CDR-SB)

### Group C: Population Features

- `age_mean` (continuous, years)
- `age_range_min_max` (tuple: [min, max] or null)
- `mmse_baseline_mean` (continuous, 0–30 scale)
- `cdr_stage_distribution` (categorical: "mild_cognitive_impairment" | "mild_dementia" | "mixed")
- `biomarker_enrichment_strategy` (categorical: "amyloid_positive" | "tau_positive" | "at_positive" | "none" | "unknown")

---

## 5. Assumptions

### Data Assumptions
1. **Trial outcome labels** are derived from:
   - Phase III advancement (binary proxy for success)
   - Primary endpoint achievement via published results or ClinicalTrials.gov
   - Assumes public trial data is accurate and complete where available

2. **Biomarker data** is assumed:
   - To follow published cutoff thresholds (e.g., APOE ε4 allele presence, plasma p-tau217 >81 pg/mL for amyloid-positive enrichment) unless trial-specific thresholds are documented
   - CSF and plasma assays are normalized to standard methods (Lumipulse, Elecsys, or mass spectrometry) with assumption that cross-assay variation is minimal
   - Missing biomarker data is treated as "not measured" rather than "negative" (confidence flag adjusts accordingly)

3. **Historical trial data** quality:
   - Trials included in training set are representative of modern Phase II AD trials (roughly 2010–2025)
   - Regulatory landscape, drug mechanisms, and patient populations are comparable to current trial designs
   - Assumes no major shifts in trial design paradigms (e.g., if amyloid hypothesis pivot occurs, model retraining is required)

### Model Assumptions
1. **Binary success label** is the only outcome:
   - Does not predict degree of efficacy (e.g., % slowing of decline), only advancement likelihood
   - Does not model safety endpoints separately (assumes safety review integrated into advancement decision)

2. **Feature independence** (for baseline models like logistic regression):
   - Features are treated as independent inputs to the model
   - Multicollinearity (e.g., APOE ε4 and plasma p-tau217 correlation) is managed via feature scaling and regularization
   - Does not explicitly model biomarker interactions

3. **Interpretability** is prioritized:
   - Baseline models (logistic regression, decision trees) are chosen for transparency
   - Neural network ensembles are secondary; rule-based models come first
   - Feature importance is derived from model coefficients or tree splits, not SHAP or other black-box explainers (though SHAP can be added later)

### Business Assumptions
1. **Customer context:**
   - Users are CNS-focused investors, biotech BD teams, or regulatory consultants
   - They understand the NIA-AA framework and biomarker terminology
   - They expect 70% success probability to represent "fundable" trials, <40% to represent "high risk"

2. **Confidence thresholds:**
   - Scores above 0.70 with HIGH confidence are suitable for investment memos
   - Scores in 0.40–0.70 MEDIUM confidence range require human review
   - Scores below 0.40 with LOW confidence are suitable for "red flag" warnings only

3. **Update frequency:**
   - Model is retrained quarterly as new trial outcomes accumulate
   - Biomarker cutoffs are reviewed biannually against published literature (e.g., new NIA-AA guidance)

### Scope Limitations
1. **v1 Coverage:**
   - Alzheimer's Disease only; ALS and Epilepsy will follow in v2
   - Phase II trials only; Phase I and Phase III require separate models
   - Does NOT include:
     - Safety risk scoring (ARIA monitoring is mentioned but not quantified)
     - Cost or timeline predictions
     - Regulatory approval likelihood beyond Phase III advancement
     - Patient dropout or compliance modeling

2. **Data Limitations:**
   - Training dataset is initially synthetic (based on biomarker logic rules) then enriched with public trial data
   - Public data availability varies by trial; not all trials have complete biomarker data published
   - Proprietary pharmaceutical trial data is not included (model is limited to published/public sources)

---

## 6. Success Criteria for Model Development

The model is considered **ready for pilot deployment** when it meets the following:

- [ ] **Baseline Model Performance**
  - Logistic Regression AUC ≥ 0.72 on validation set
  - Accuracy ≥ 0.70 on held-out test set
  - Calibration error ≤ 0.1 (Brier score)

- [ ] **Interpretability**
  - Top 5 features explained in plain English for ≥90% of predictions
  - Model agrees with domain expert judgment on ≥80% of trial assessments
  - Feature importance coefficients are stable across cross-validation folds

- [ ] **Biomarker Logic Alignment**
  - When model scores trials with high APOE ε4 + amyloid positive + elevated p-tau217, success probability is ≥0.70
  - When model scores trials with borderline biomarkers or missing data, success probability is 0.40–0.60 with appropriate confidence downgrade

- [ ] **Output Format Compliance**
  - All predictions return JSON with required fields (trial_success_probability, risk_tier, top_5_feature_importance, etc.)
  - Confidence flags adjust correctly based on missing data
  - Biomarker explanations are generated automatically and validated by domain expert review

- [ ] **Documentation**
  - README explains assumptions, data sources, and biomarker cutoffs
  - Feature catalog maps each column to biomarker logic sheets
  - Validation report documents model agreement with known trial outcomes (lecanemab, etc.)

---

## 7. Next Steps

1. **Finalize Feature Catalog** (Feature/biomarker_feature_catalog.md)
   - Map each entry in Genivra biomarker logic sheets to ML input column
   - Define encoding rules and cutoff thresholds

2. **Build Synthetic Training Dataset** (Data/Raw/synthetic_ad_trials_v1.csv)
   - 200–500 synthetic AD Phase II trials with deterministic labels derived from biomarker logic
   - Include ~100 public trial references (lecanemab, etc.) as validation anchors

3. **Implement Baseline Models** (Models/)
   - Logistic Regression with L2 regularization
   - Decision Tree classifier
   - Rule-based scorer (encodes biomarker logic directly)

4. **Validation Study** (Evaluation/)
   - Score 10–15 public lecanemab trials and document agreement/disagreement with known outcomes
   - Publish validation report to portfolio

5. **API / Output Generation** (Scripts/)
   - Build `generate_trial_score.py` that returns JSON with all required fields
   - Integrate confidence flag logic based on data completeness

---

## 8. References

### NIA-AA Framework
- NIA-AA AT(N) Classification (free full text: PMC5958625)
- NIA-AA Research Framework for Alzheimer's disease biomarkers

### Biomarker Evidence (Key Publications)
- **Plasma p-tau217:** Nat Med 2025 (blood biomarkers predict dementia, s41591-025-03605-x)
- **Plasma biomarker pretest probability:** Nat Med 2024 (s43587-024-00731-y)
- **FDA Clearance:** Lumipulse p-tau217/Aβ1-42 ratio (May 16, 2025 press release)

### Lecanemab Phase II Reference
- **Trial ID:** NCT03887455, NCT04468659
- **Published:** ClinicalTrials.gov, FDA briefing documents
- **Endpoint:** CDR-SB decline slowing 35% vs. placebo

### Design Standards
- FDA Statistical Review (accessdata.fda.gov)
- ICER AD Pharmacological Treatment Report (2024)

---

**Document Owner:** Genivra ML Team  
**Next Review Date:** May 20, 2026
