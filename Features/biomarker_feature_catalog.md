# Biomarker Feature Catalog: Alzheimer's Disease Phase II ML Model

**Version:** 1.0  
**Last Updated:** February 20, 2026  
**Indication:** Alzheimer's Disease  
**Trial Phase:** Phase II  
**Status:** Reference Standard

---

## Overview

This document maps **Genivra biomarker logic sheets** and trial design variables to **machine-readable ML features**. Every feature has a deterministic encoding rule, ensuring reproducible data transforms across the ML pipeline.

All encoding is idempotent: applying the same rule twice produces the same output.

---

## Feature Catalog

| # | Feature Name | Source Biomarker | Data Type | Encoding Rule | Clinical Rationale | Required |
|---|---|---|---|---|---|---|
| 1 | `apoe_e4_carrier` | APOE ε4 Genotype (Genetic) | Binary | `1` if ≥1 ε4 allele present; `0` if no ε4 alleles (e.g., e3/e3, e2/e3, e2/e2); `null` if genotype unknown | APOE ε4 is the strongest genetic risk factor for AD. Homozygous and heterozygous carriers have elevated lifetime dementia risk and faster cognitive decline. Improves trial enrichment and patient stratification. **Source:** NIA-AA AT(N) notes; PMC5958625 | Yes |
| 2 | `apoe_e4_homozygous` | APOE ε4 Genotype (Genetic) | Binary | `1` if e4/e4 genotype; `0` if heterozygous (e2/e4 or e3/e4) or no e4; `null` if genotype unknown | Homozygous e4/e4 carriers have higher risk and faster progression. May require separate monitoring/enrichment in trial design. Sensitive stratification variable. **Source:** NIA-AA, Nat Neurosci 2019 | No (optional for stratification) |
| 3 | `ptau217_high` | Plasma p-tau217 (Blood/Plasma) | Binary | `1` if plasma p-tau217 > 14.5 pg/mL (assay-specific cutoff, adjust per assay); `0` if ≤14.5 pg/mL; `null` if not measured | Plasma p-tau217 is a non-invasive biomarker for amyloid and tau pathology. Levels >14.5 pg/mL (Phospho-Tau217 assay cutoff from FDA clearance, May 2025) indicate elevated risk and support trial enrichment strategy. Predicts dementia conversion and cognitive decline (Nat Med 2025). **Source:** FDA press release May 16, 2025; Nat Med 2025 (s41591-025-03605-x) | Yes |
| 4 | `ptau217_continuous` | Plasma p-tau217 (Blood/Plasma) | Continuous | Raw value in pg/mL; `null` if not measured. No transformation applied (preserve original assay units). | Retain raw p-tau217 for models that benefit from continuous features (e.g., logistic regression with odds ratios per unit increase). Allows fine-grained risk stratification beyond binary cutoff. | No (optional, use instead of or alongside `ptau217_high`) |
| 5 | `csf_abeta42_40_ratio_low` | CSF Aβ42/Aβ40 Ratio (CSF) | Binary | `1` if CSF Aβ42/Aβ40 ratio < 0.5 (or <0.055 if reporting as Aβ42 absolute); `0` if ratio ≥ 0.5; `null` if CSF not available | Low CSF Aβ42/Aβ40 ratio (<0.5) indicates amyloid pathology and aligns with NIA-AA "A+" biomarker status. Predicts disease progression and trial benefit. Invasive (lumbar puncture) but highly specific. **Source:** NIA-AA Research Framework (PMC5958625); ClinicalTrials.gov lecanemab trials | No (if plasma biomarkers available) |
| 6 | `csf_abeta42_40_ratio_continuous` | CSF Aβ42/Aβ40 Ratio (CSF) | Continuous | Raw ratio value (e.g., 0.45, 0.38); no transformation. `null` if not measured. | Preserve raw CSF ratio for dose–response type modeling and sensitivity analyses. Allows models to detect threshold effects or non-linear relationships. | No (optional) |
| 7 | `csf_ptau_elevated` | CSF p-tau181 or p-tau217 (CSF) | Binary | `1` if CSF p-tau > 79 pg/mL (p-tau181 threshold per NIA-AA) or local assay cutoff; `0` if ≤79 pg/mL; `null` if not measured | Elevated CSF p-tau indicates tau pathology alignment with NIA-AA "T+" criterion. Supports disease staging and enrichment in tau-targeting trials. More specific for tau pathology than blood p-tau alone. **Source:** NIA-AA Research Framework (PMC5958625) | No (if plasma p-tau available) |
| 8 | `amyloid_pet_positive` | Amyloid PET Imaging | Binary | `1` if Amyloid PET SUVR > 1.2 (or >0.79 for 18F-Florbetapir) or if radiology report explicitly states "amyloid positive"; `0` if SUVR ≤ 1.2 / "amyloid negative"; `null` if PET not performed | Amyloid PET positivity is the NIA-AA "A+" criterion. Identifies amyloid-positive patients for enrichment in anti-amyloid monoclonal antibody trials (e.g., lecanemab, donanemab). Predicts disease progression and trial response. **Source:** NIA-AA Research Framework (PMC5958625); ClinicalTrials.gov lecanemab (NCT03887455) | Yes |
| 9 | `tau_pet_positive` | Tau PET Imaging | Binary | `1` if Tau PET SUVR > 1.3 (assay-specific; adjust per tracer) in predefined regions or if report states "tau positive"; `0` if SUVR ≤ 1.3; `null` if not performed | Tau PET indicates "T+" NIA-AA status and regional tau burden. Useful for tau-targeting drug trials and staging. Less universally performed than amyloid PET in Phase II trials; treated as optional enrichment variable. **Source:** NIA-AA Research Framework (PMC5958625) | No |
| 10 | `hippocampal_atrophy_mri` | Hippocampal Volume (MRI) | Continuous | Raw hippocampal volume in mm³ as measured by automated segmentation (e.g., FreeSurfer, SPM). Recommend percent atrophy relative to age/sex-standardized norm: `(measured_vol / expected_vol) * 100`. Report both raw and %-norm. `null` if MRI not performed. | Hippocampal atrophy is an NIA-AA "N+" neurodegeneration marker. Correlates with cognitive impairment severity and baseline decline rate. Helps stratify patient risk and predict treatment response. Structural imaging monitors safety (ARIA on MRI). **Source:** NIA-AA Research Framework (PMC5958625); ICER 2024 report | No |
| 11 | `hippocampal_atrophy_binary` | Hippocampal Volume (MRI) | Binary | `1` if hippocampal volume < 10th percentile for age/sex-matched population (criteria varies: often <4.0 cm³ in older adults at MCI/dementia stage); `0` if volume ≥ 10th percentile; `null` if MRI not available | Dichotomized atrophy for interpretability in decision trees or logistic regression. Allows simple stratification: "moderate-to-severe atrophy" vs. "mild or absent atrophy." | No (optional alongside continuous feature) |
| 12 | `age_mean` | Baseline Participant Age | Continuous | Mean (average) age of trial cohort in years. If individual ages available, compute `age_mean = sum(all_participant_ages) / n_participants`. If only range provided, use midpoint. Report to 1 decimal place. `null` if not reported. | Age influences AD onset, progression rate, and trial response. Younger cohorts (55–65) enrich for genetic/autosomal dominant AD; older cohorts (70+) represent sporadic AD. Biomarker cutoffs may differ by age. Affects safety risk (ARIA in older patients). **Source:** Participant baseline in trial protocol or published results | Yes |
| 13 | `baseline_mmse` | Mini-Mental State Exam (MMSE) Score | Continuous | Raw MMSE score at baseline visit, range 0–30 (higher = better cognition). No transformation applied. `null` if not assessed. | Baseline cognitive severity predicts trial response and decline trajectory. MMSE 20–26 = mild cognitive impairment; MMSE 16–20 = mild dementia. Determines enrollment eligibility and stratification. Model uses this to predict who will show treatment benefit. **Source:** Trial protocol, baseline assessments, ClinicalTrials.gov | Yes |
| 14 | `baseline_moca` | Montreal Cognitive Assessment (MoCA) | Continuous | Raw MoCA score at baseline, range 0–30. No transformation. `null` if not used or if MMSE is primary. | Alternative (or complementary) to MMSE; more sensitive to MCI. Some trials use MoCA as primary cognitive endpoint. If both MMSE and MoCA available, include both and let model weight. | No |
| 15 | `cdr_baseline` | Clinical Dementia Rating (CDR) | Continuous | Raw CDR sum-of-boxes score at baseline, range 0–18. Record to 0.5-point precision (e.g., 1.0, 1.5, 2.0). `null` if not administered. | CDR-SB (sum of boxes) is primary endpoint in many AD trials (e.g., lecanemab). Baseline CDR predicts trajectory and treatment response. Values 0–2 = MCI to mild dementia range typical for Phase II enrichment. | Yes (preferred over MMSE for endpoint trials) |
| 16 | `trial_sample_size` | Study Design / Enrollment | Continuous | Planned sample size (n) at trial initiation. Integer value. If multi-arm trial, report total planned n across all arms. `null` if not specified. | Larger trials reduce random variation and are more likely to detect true effects. Phase II trials typically enroll 100–400 subjects. Sample size interacts with efficacy magnitude to determine Phase III advancement. Under-powered trials fail despite real signals. **Source:** Trial protocol, ClinicalTrials.gov | Yes |
| 17 | `trial_duration_weeks` | Study Design / Duration | Continuous | Planned trial duration in weeks from first participant enrolled to final assessment window close. Convert months if provided: `weeks = months * 4.33`. Round to nearest week. `null` if duration not pre-defined. | Longer Phase II trials improve ability to detect cognitive decline differences. Typical Phase II durations: 12–52 weeks. Very short trials (<12 weeks) less likely to show clearer endpoints. Interacts with expected decline rate. **Source:** Trial protocol | Yes |
| 18 | `endpoint_type` | Endpoint Classification | Categorical | One of: `"objective"`, `"subjective"`, `"mixed"`. **Objective:** biomarker or imaging endpoint (PET, MRI, CSF). **Subjective:** cognitive scale (MMSE, MoCA), caregiver report, or symptom survey. **Mixed:** combination (e.g., CDR-SB + amyloid PET biomarker change). | Endpoint type influences trial success likelihood. Objective endpoints (imaging) often fail due to high variability; subjective cognitive scales (CDR-SB) have high inter-rater variance but established historical success. Model learns which endpoint types correlate with Phase III advancement. **Source:** Trial protocol; ClinicalTrials.gov definition | Yes |
| 19 | `primary_endpoint_name` | Endpoint Specification | Categorical | String identifier: one of `"CDR-SB"`, `"ADAS-Cog"`, `"MMSE"`, `"ADCOMS"`, `"amyloid_pet_suvr"`, `"tau_pet_suvr"`, `"cognitive_decline_mci_progression"`, `"biomarker_change"`, or `"other"`. | Identifies which specific cognitive or biomarker scale is primary outcome. Different endpoints have different historical success rates. CDR-SB and ADAS-Cog have strong precedent (lecanemab, solanezumab). Novel endpoints carry risk. **Source:** Trial protocol | Yes |
| 20 | `biomarker_enrichment_strategy` | Trial Inclusion Strategy | Categorical | One of: `"amyloid_positive"`, `"tau_positive"`, `"at_positive"`, `"cognitive_only"`, `"none"`, `"unknown"`. **amyloid_positive:** requires amyloid PET+ or CSF Aβ42↓. **tau_positive:** requires tau PET+ or CSF p-tau↑. **at_positive:** requires both amyloid AND tau biomarkers. **cognitive_only:** no biomarker requirement, enrolls on cognitive criteria alone. **none:** no structured enrichment. **unknown:** not specified in trial design. | Biomarker enrichment increases likelihood of detecting drug effect by enrolling patients with defined pathology. Amyloid-positive enrichment is standard in anti-amyloid trials; tau-positive in tau-targeting trials. No enrichment ("cognitive only") increases heterogeneity and failure risk. **Source:** Trial protocol; NIA-AA AT(N) framework | Yes |
| 21 | `number_of_arms` | Study Design / Structure | Continuous | Integer count of parallel treatment arms (e.g., 2 for drug vs. placebo, 3 for two doses + placebo). `null` if open-label (single arm). | Multi-arm trials increase sample size demand but allow adaptive design or dose-ranging. Single-arm trials are rare in Phase II AD unless historically controlled. Structure influences statistical power. | No |
| 22 | `randomization_ratio` | Study Design / Randomization | Categorical | One of: `"1:1"` (balanced, equal arms), `"2:1"` (2:1 drug:placebo), `"3:1"`, or `"open_label"` (no randomization). | Randomization ratio affects power to detect effect. 1:1 is standard; 2:1 enriches drug arm for faster efficacy signal. Open-label trials are prone to bias; rare in modern AD Phase II. | No |

---

## Encoding Details & Implementation

### Genetic Biomarkers

#### `apoe_e4_carrier` (Binary)
```python
# Pseudo-code encoding logic:
def encode_apoe_e4_carrier(genotype_string: str) -> Optional[int]:
    """
    Convert APOE genotype (e.g., "e3/e4", "e4/e4", "e2/e3") to binary carrier status.
    """
    if genotype_string is None or genotype_string.lower() == "unknown":
        return None
    
    genotype = genotype_string.lower().replace(" ", "")
    # Check if any e4 allele present
    if "e4" in genotype:
        return 1
    else:
        return 0

# Examples:
encode_apoe_e4_carrier("e3/e4") → 1  # heterozygous carrier
encode_apoe_e4_carrier("e4/e4") → 1  # homozygous carrier
encode_apoe_e4_carrier("e2/e3") → 0  # non-carrier
encode_apoe_e4_carrier("e3/e3") → 0  # non-carrier
encode_apoe_e4_carrier(None)      → None  # unknown
```

#### `apoe_e4_homozygous` (Binary, Optional)
```python
def encode_apoe_e4_homozygous(genotype_string: str) -> Optional[int]:
    """
    Return 1 only if both alleles are e4 (e4/e4), else 0 or null.
    """
    if genotype_string is None or "unknown" in genotype_string.lower():
        return None
    
    genotype = genotype_string.lower().replace(" ", "")
    
    if genotype == "e4/e4":
        return 1
    else:
        return 0

# Examples:
encode_apoe_e4_homozygous("e4/e4") → 1
encode_apoe_e4_homozygous("e2/e4") → 0
encode_apoe_e4_homozygous("e3/e4") → 0
```

### Blood Biomarkers

#### `ptau217_high` (Binary)
```python
def encode_ptau217_high(ptau217_value: Optional[float], 
                        cutoff_pg_ml: float = 14.5) -> Optional[int]:
    """
    Classify plasma p-tau217 as high (≥cutoff) or low (<cutoff).
    Cutoff default is 14.5 pg/mL per FDA Lumipulse clearance (May 2025).
    Adjust cutoff per assay platform if needed.
    """
    if ptau217_value is None:
        return None
    
    if ptau217_value > cutoff_pg_ml:
        return 1
    else:
        return 0

# Examples (cutoff=14.5 pg/mL):
encode_ptau217_high(18.5)  → 1  # elevated
encode_ptau217_high(12.0)  → 0  # normal
encode_ptau217_high(None)  → None
```

#### `ptau217_continuous` (Continuous)
```python
def encode_ptau217_continuous(ptau217_value: Optional[float]) -> Optional[float]:
    """
    Preserve raw plasma p-tau217 in pg/mL.
    No log-transformation; no standardization (scaling happens in model preprocessing).
    """
    return ptau217_value  # return as-is or None

# Examples:
encode_ptau217_continuous(18.5)  → 18.5
encode_ptau217_continuous(None)  → None
```

### CSF Biomarkers

#### `csf_abeta42_40_ratio_low` (Binary)
```python
def encode_csf_abeta42_40_ratio_low(ratio: Optional[float], 
                                    cutoff: float = 0.5) -> Optional[int]:
    """
    Classify CSF Aβ42/Aβ40 ratio as LOW (pathological) if < cutoff.
    Standard cutoff: 0.5 per NIA-AA.
    Note: Some labs report as Aβ42 absolute (pg/mL); use ~500 pg/mL as cutoff if raw Aβ42 only.
    """
    if ratio is None:
        return None
    
    if ratio < cutoff:
        return 1  # low ratio = pathological = amyloid positive
    else:
        return 0  # normal ratio

# Examples (cutoff=0.5):
encode_csf_abeta42_40_ratio_low(0.42)  → 1  # low
encode_csf_abeta42_40_ratio_low(0.60)  → 0  # normal
encode_csf_abeta42_40_ratio_low(None)  → None
```

### Imaging Biomarkers

#### `amyloid_pet_positive` (Binary)
```python
def encode_amyloid_pet_positive(suvr: Optional[float] = None,
                                radiology_text: Optional[str] = None,
                                suvr_cutoff: float = 1.2) -> Optional[int]:
    """
    Classify Amyloid PET as positive (1) if SUVR > cutoff or radiology report says "positive".
    SUVR cutoff depends on tracer:
    - 18F-Florbetapir: SUVR > 0.79 (alternative: >1.1 in some centers)
    - 18F-Florbetaben: SUVR > 1.2
    - 11C-PiB: SUVR > 1.5
    Default cutoff 1.2 is conservative middle ground.
    
    If only qualitative assessment available, parse radiology report.
    """
    # Check quantitative SUVR first
    if suvr is not None:
        if suvr > suvr_cutoff:
            return 1
        else:
            return 0
    
    # Fall back to qualitative radiology assessment
    if radiology_text is not None:
        text_lower = radiology_text.lower()
        if "positive" in text_lower or "elevated" in text_lower:
            return 1
        elif "negative" in text_lower or "normal" in text_lower:
            return 0
    
    # If neither available, return None
    return None

# Examples:
encode_amyloid_pet_positive(suvr=1.35)  → 1  # positive
encode_amyloid_pet_positive(suvr=1.10)  → 0  # negative
encode_amyloid_pet_positive(radiology_text="Amyloid PET positive") → 1
encode_amyloid_pet_positive(suvr=None, radiology_text=None) → None
```

#### `hippocampal_atrophy_binary` (Binary, derived)
```python
def encode_hippocampal_atrophy_binary(volume_mm3: Optional[float],
                                      age_years: Optional[float],
                                      cutoff_mm3: float = 4000.0) -> Optional[int]:
    """
    Classify as atrophic (1) if volume < cutoff (typically <4.0 cm³ = 4000 mm³).
    Cutoff varies by age and sex; for simplicity, use 4000 mm³ for adults 70+.
    Ideally, compare to age/sex-adjusted norms (FreeSurfer provides these).
    
    Alternative: if %-relative-to-norm available, use <10th percentile as cutoff.
    """
    if volume_mm3 is None:
        return None
    
    # Simple cutoff approach
    if volume_mm3 < cutoff_mm3:
        return 1  # atrophic
    else:
        return 0  # normal

# Examples:
encode_hippocampal_atrophy_binary(3500.0)  → 1  # atrophic
encode_hippocampal_atrophy_binary(4500.0)  → 0  # normal
encode_hippocampal_atrophy_binary(None) → None
```

### Cognitive/Clinical Features

#### `age_mean` (Continuous)
```python
def encode_age_mean(age_list: List[float]) -> Optional[float]:
    """
    Compute mean age of trial cohort.
    Input: list of individual participant ages.
    Output: average age (float), rounded to 1 decimal place.
    """
    if not age_list or all(a is None for a in age_list):
        return None
    
    valid_ages = [a for a in age_list if a is not None and a > 0]
    if len(valid_ages) == 0:
        return None
    
    mean_age = sum(valid_ages) / len(valid_ages)
    return round(mean_age, 1)

# Alternatively, if only range provided:
def encode_age_mean_from_range(min_age: float, max_age: float) -> float:
    """Use midpoint if individual ages unavailable."""
    return (min_age + max_age) / 2.0

# Examples:
encode_age_mean([65, 70, 72, 68]) → 68.8
encode_age_mean_from_range(60, 80) → 70.0
```

#### `baseline_mmse` (Continuous)
```python
def encode_baseline_mmse(mmse_score: Optional[float]) -> Optional[float]:
    """
    Preserve raw MMSE score (range 0–30).
    No transformation.
    Validate: 0 ≤ score ≤ 30.
    """
    if mmse_score is None:
        return None
    
    if not (0 <= mmse_score <= 30):
        raise ValueError(f"MMSE score {mmse_score} out of valid range [0, 30]")
    
    return mmse_score

# Examples:
encode_baseline_mmse(24.0)  → 24.0
encode_baseline_mmse(18.5)  → 18.5
encode_baseline_mmse(None)  → None
```

#### `cdr_baseline` (Continuous)
```python
def encode_cdr_baseline(cdr_sum_of_boxes: Optional[float]) -> Optional[float]:
    """
    Preserve raw CDR sum-of-boxes score (range 0–18, in 0.5-point increments).
    """
    if cdr_sum_of_boxes is None:
        return None
    
    if not (0 <= cdr_sum_of_boxes <= 18):
        raise ValueError(f"CDR-SB {cdr_sum_of_boxes} out of valid range [0, 18]")
    
    return round(cdr_sum_of_boxes, 1)

# Examples:
encode_cdr_baseline(1.5)   → 1.5
encode_cdr_baseline(5.0)   → 5.0
encode_cdr_baseline(None)  → None
```

### Trial Design Features

#### `trial_sample_size` (Continuous)
```python
def encode_trial_sample_size(planned_n: Optional[int]) -> Optional[int]:
    """
    Preserve planned sample size (integer).
    For multi-arm trials, report total n across all arms.
    """
    if planned_n is None or planned_n <= 0:
        return None
    
    return int(planned_n)

# Examples:
encode_trial_sample_size(250)  → 250
encode_trial_sample_size(None) → None
```

#### `trial_duration_weeks` (Continuous)
```python
def encode_trial_duration_weeks(duration: Optional[float], 
                                unit: str = "weeks") -> Optional[float]:
    """
    Convert trial duration to weeks.
    Input unit can be: "weeks", "months", "days", "years".
    """
    if duration is None or duration <= 0:
        return None
    
    conversion_factors = {
        "weeks": 1.0,
        "months": 4.33,  # 1 month ≈ 4.33 weeks
        "days": 1/7.0,
        "years": 52.14,
    }
    
    if unit not in conversion_factors:
        raise ValueError(f"Unknown unit: {unit}")
    
    weeks = duration * conversion_factors[unit]
    return round(weeks, 0)  # round to nearest week

# Examples:
encode_trial_duration_weeks(26, unit="weeks") → 26.0
encode_trial_duration_weeks(6, unit="months")  → 26.0
encode_trial_duration_weeks(None) → None
```

#### `endpoint_type` (Categorical)
```python
def encode_endpoint_type(endpoint_description: Optional[str]) -> Optional[str]:
    """
    Classify endpoint type as: "objective", "subjective", or "mixed".
    
    Objective: PET/MRI imaging, CSF biomarker, pathologic confirmation.
    Subjective: cognitive scales (MMSE, CDR-SB, ADAS-Cog), caregiver/patient report.
    Mixed: both objective and subjective (e.g., CDR-SB + amyloid PET).
    """
    if endpoint_description is None:
        return None
    
    endpoint_lower = endpoint_description.lower()
    
    # Define keywords
    objective_keywords = ["pet", "mri", "imaging", "biomark", "csf", "amyloid", "tau"]
    subjective_keywords = ["cdr-sb", "adas-cog", "mmse", "moca", "Scale", "cognitive", "decline"]
    
    has_objective = any(kw in endpoint_lower for kw in objective_keywords)
    has_subjective = any(kw in endpoint_lower for kw in subjective_keywords)
    
    if has_objective and has_subjective:
        return "mixed"
    elif has_objective:
        return "objective"
    elif has_subjective:
        return "subjective"
    else:
        return None  # ambiguous

# Examples:
encode_endpoint_type("CDR-SB decline over 18 months") → "subjective"
encode_endpoint_type("Amyloid PET SUVR change + CDR-SB") → "mixed"
encode_endpoint_type("Time to MCI conversion on MRI") → "objective"
encode_endpoint_type(None) → None
```

#### `primary_endpoint_name` (Categorical)
```python
def encode_primary_endpoint_name(endpoint_string: Optional[str]) -> Optional[str]:
    """
    Map endpoint description to standardized category.
    Allowed values: "CDR-SB", "ADAS-Cog", "MMSE", "ADCOMS", "amyloid_pet_suvr", 
                   "tau_pet_suvr", "cognitive_decline_mci_progression", "biomarker_change", "other"
    """
    if endpoint_string is None:
        return None
    
    endpoint_lower = endpoint_string.lower()
    
    # Direct mapping
    mappings = {
        "cdr-sb": "CDR-SB",
        "adas-cog": "ADAS-Cog",
        "mmse": "MMSE",
        "moca": "MOCA",
        "adcoms": "ADCOMS",
        "amyloid": "amyloid_pet_suvr",
        "tau_pet": "tau_pet_suvr",
        "mci_conversion": "cognitive_decline_mci_progression",
        "progression": "cognitive_decline_mci_progression",
        "biomarker": "biomarker_change",
    }
    
    for key, value in mappings.items():
        if key in endpoint_lower:
            return value
    
    return "other"

# Examples:
encode_primary_endpoint_name("CDR-SB decline ≥35%") → "CDR-SB"
encode_primary_endpoint_name("Amyloid PET SUVR change") → "amyloid_pet_suvr"
encode_primary_endpoint_name("Time to MCI progression") → "cognitive_decline_mci_progression"
```

#### `biomarker_enrichment_strategy` (Categorical)
```python
def encode_biomarker_enrichment_strategy(trial_inclusion: Optional[str]) -> Optional[str]:
    """
    Classify trial biomarker enrichment strategy.
    Allowed: "amyloid_positive", "tau_positive", "at_positive", "cognitive_only", "none", "unknown"
    """
    if trial_inclusion is None:
        return "unknown"
    
    text_lower = trial_inclusion.lower()
    
    # Check for specific patterns
    if ("amyloid+" in text_lower or "amyloid_positive" in text_lower or "amyloid positive" in text_lower) and \
       ("tau+" not in text_lower and "tau_positive" not in text_lower):
        return "amyloid_positive"
    
    elif ("tau+" in text_lower or "tau_positive" in text_lower or "tau positive" in text_lower) and \
         ("amyloid+" not in text_lower and "amyloid_positive" not in text_lower):
        return "tau_positive"
    
    elif ("amyloid+" in text_lower and "tau+" in text_lower) or ("at+" in text_lower or "at(n)" in text_lower):
        return "at_positive"
    
    elif "no biomarker" in text_lower or "cognitive only" in text_lower:
        return "cognitive_only"
    
    elif "no enrichment" in text_lower:
        return "none"
    
    else:
        return "unknown"

# Examples:
encode_biomarker_enrichment_strategy("Amyloid-positive patients required") → "amyloid_positive"
encode_biomarker_enrichment_strategy("AT(N) positive (amyloid + tau)") → "at_positive"
encode_biomarker_enrichment_strategy("No biomarker requirement") → "cognitive_only"
encode_biomarker_enrichment_strategy(None) → "unknown"
```

---

## Data Validation Rules

All features are subject to the following validation checks:

1. **Type Correctness:** Binary features ∈ {0, 1, None}; continuous features are floats or None; categorical features match allowed values.

2. **Range Validation:**
   - Age: 18 ≤ age ≤ 120
   - MMSE: 0 ≤ score ≤ 30
   - CDR-SB: 0 ≤ score ≤ 18
   - Sample size: n > 0
   - Duration: weeks > 0

3. **Null Handling:** Null (missing) values are preserved as `None` and never imputed until model training phase.

4. **Consistency Checks:**
   - If `amyloid_pet_positive = 1`, then `biomarker_enrichment_strategy` should **not** be `"cognitive_only"` or `"none"` (inconsistent)
   - If `trial_sample_size < 50`, flag as underpowered (warning, not error)
   - If `trial_duration_weeks < 12`, flag as very short (may have insufficient signal)

---

## References

- **NIA-AA AT(N):** PMC5958625 (full text)
- **Plasma p-tau217:** Nat Med 2025 (s41591-025-03605-x)
- **FDA Lumipulse clearance:** Press release May 16, 2025
- **Lecanemab Phase II:** ClinicalTrials.gov (NCT03887455)
- **CSF biomarker cutoffs:** NIA-AA Research Framework and CDR-SB endpoint literature

---

**Document Owner:** Genivra ML Features Team  
**Next Review Date:** May 20, 2026  
**Version Control:** See GitHub for commit history and updates
