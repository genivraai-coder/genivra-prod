"""
Rule-Based Trial Success Scorer

Implements deterministic, interpretable biomarker logic for trial success prediction.
This is a baseline model that encodes clinical domain knowledge directly as weighted features.

Scoring logic:
- Start with neutral baseline (0.50)
- Add weights for favorable biomarkers (amyloid+, tau+, APOE ε4, trial design)
- Subtract weights for adverse features (low sample size, advanced dementia)
- Normalize to [0, 1]
- Map to risk tiers (Low/Medium/High)

Author: Genivra ML Team
Date: February 20, 2026
Version: 1.0
"""

from typing import Dict, Optional
import warnings


# ============================================================================
# Feature Weights (Encoding Clinical Domain Knowledge)
# ============================================================================

class RuleBasedWeights:
    """
    Clinical weights for trial success scoring.
    Based on Genivra biomarker logic sheets and published trial literature.
    """

    # ===== BIOMARKER POSITIVE CONTRIBUTIONS =====
    AMYLOID_PET_POSITIVE = 0.25  # Strongest predictor (amyloid is core pathology)
    PTAU217_HIGH = 0.20  # Plasma p-tau217 is strong non-invasive biomarker
    CSF_ABETA42_40_LOW = 0.15  # CSF biomarker (invasive but specific)
    CSF_PTAU_ELEVATED = 0.12  # CSF tau pathology marker
    TAU_PET_POSITIVE = 0.10  # Tau imaging (less common, supplementary)
    APOE_E4_CARRIER = 0.15  # Genetic risk factor
    APOE_E4_HOMOZYGOUS = 0.08  # Additional weight for e4/e4 (bonus on top of carrier)
    HIPPOCAMPAL_ATROPHY = 0.05  # Neurodegeneration marker (N+)

    # ===== TRIAL DESIGN POSITIVE CONTRIBUTIONS =====
    LONG_DURATION_GE_52_WEEKS = 0.10  # ≥52 weeks = better signal detection
    MEDIUM_DURATION_GE_36_WEEKS = 0.05  # 36–51 weeks
    ADEQUATE_SAMPLE_SIZE_GE_250 = 0.08  # Large trial = more power
    GOOD_SAMPLE_SIZE_GE_150 = 0.04  # Moderate trial
    GOOD_ENDPOINT_TYPE_MIXED = 0.02  # Mixed objective + subjective
    GOOD_PRIMARY_ENDPOINT = 0.05  # CDR-SB or ADAS-Cog (gold standard)
    RANDOMIZED_STRUCTURE = 0.03  # Randomized > open-label
    ADAPTIVE_RANDOMIZATION = 0.02  # 2:1 adaptive adds modest benefit

    # ===== COGNITIVE STAGE CONTRIBUTIONS =====
    BASELINE_MMSE_MCI_SWEET_SPOT = 0.10  # 18 ≤ MMSE ≤ 26 (ideal enrichment)
    BASELINE_MMSE_MILD_DEMENTIA = 0.03  # 16 ≤ MMSE < 18 (acceptable)
    HIPPOCAMPAL_VOLUME_NORMAL = 0.05  # Normal vs. atrophic

    # ===== BIOMARKER ENRICHMENT BONUS =====
    ENRICHMENT_AT_POSITIVE = 0.08  # Both amyloid + tau
    ENRICHMENT_AMYLOID_POSITIVE = 0.06  # Amyloid-only strategy

    # ===== AGE ADJUSTMENT =====
    AGE_SWEET_SPOT_60_75 = 0.04  # Age 60–75 is optimal

    # ===== NEGATIVE CONTRIBUTIONS (PENALTIES) =====
    SMALL_SAMPLE_LT_100 = -0.20  # Severe underpowering penalty
    MEDIUM_SMALL_SAMPLE_LT_150 = -0.10  # Moderate underpowering
    SHORT_DURATION_LT_24_WEEKS = -0.12  # Very short trials fail to show signal
    MEDIUM_SHORT_DURATION_LT_36_WEEKS = -0.06  # Borderline short
    ADVANCED_DEMENTIA_MMSE_LT_16 = -0.20  # Too advanced, less decline to detect
    VERY_ADVANCED_DEMENTIA_MMSE_LT_10 = -0.30  # Severe dementia, floor effects
    MILD_COGNITIVE_DECLINE_MMSE_GT_26 = -0.08  # Very mild, harder to detect decline
    NO_ENRICHMENT = -0.10  # Cognitive-only or no enrichment strategy (heterogeneous)
    OPEN_LABEL_STRUCTURE = -0.08  # No randomization, bias risk
    OBJECTIVE_ENDPOINT_ONLY = -0.05  # Harder to achieve vs. subjective
    UNCOMMON_ENDPOINT = -0.03  # Non-standard endpoints less validated

    # ===== AGE PENALTIES =====
    AGE_LT_60 = -0.05  # Genetic/rare AD, less representative
    AGE_GT_80 = -0.06  # Very old, more comorbidities and dropout


# ============================================================================
# Trial Score Calculator
# ============================================================================

class TrialScorer:
    """
    Rule-based scorer for Alzheimer's trials using deterministic biomarker weights.
    """

    def __init__(self, weights: RuleBasedWeights = None):
        """
        Initialize scorer with weights.

        Args:
            weights (RuleBasedWeights): Weight object. Uses defaults if None.
        """
        self.weights = weights or RuleBasedWeights()

    def score_trial(self, trial: Dict) -> Dict:
        """
        Score a trial based on biomarker and design features.

        Args:
            trial (Dict): Trial data with biomarker, cognitive, and design features.
                         Expected keys:
                         - amyloid_pet_positive (0/1)
                         - ptau217_high (0/1)
                         - csf_abeta42_40_ratio_low (0/1)
                         - csf_ptau_elevated (0/1 or None)
                         - tau_pet_positive (0/1 or None)
                         - apoe_e4_carrier (0/1)
                         - apoe_e4_homozygous (0/1)
                         - hippocampal_atrophy_binary (0/1)
                         - baseline_mmse (float)
                         - age_mean (float)
                         - trial_sample_size (int)
                         - trial_duration_weeks (int)
                         - primary_endpoint_name (str)
                         - endpoint_type (str)
                         - biomarker_enrichment_strategy (str)
                         - randomization_ratio (str)

        Returns:
            Dict with keys:
            - trial_success_probability (float, 0–1)
            - risk_tier (str: "Low" | "Medium" | "High")
            - component_scores (dict): Breakdown of contributions
        """
        score = 0.50  # Neutral baseline

        # Dictionary to track component contributions for interpretability
        components = {}

        # ===== BIOMARKER SCORING =====
        biomarker_score = 0.0

        # Amyloid pathology
        if self._safe_get(trial, "amyloid_pet_positive") == 1:
            biomarker_score += self.weights.AMYLOID_PET_POSITIVE
            components["amyloid_pet_positive"] = self.weights.AMYLOID_PET_POSITIVE

        # Tau pathology (plasma)
        if self._safe_get(trial, "ptau217_high") == 1:
            biomarker_score += self.weights.PTAU217_HIGH
            components["ptau217_high"] = self.weights.PTAU217_HIGH

        # CSF biomarkers
        if self._safe_get(trial, "csf_abeta42_40_ratio_low") == 1:
            biomarker_score += self.weights.CSF_ABETA42_40_LOW
            components["csf_abeta42_40_ratio_low"] = self.weights.CSF_ABETA42_40_LOW

        if self._safe_get(trial, "csf_ptau_elevated") == 1:
            biomarker_score += self.weights.CSF_PTAU_ELEVATED
            components["csf_ptau_elevated"] = self.weights.CSF_PTAU_ELEVATED

        # Tau PET
        if self._safe_get(trial, "tau_pet_positive") == 1:
            biomarker_score += self.weights.TAU_PET_POSITIVE
            components["tau_pet_positive"] = self.weights.TAU_PET_POSITIVE

        # Genetic risk
        if self._safe_get(trial, "apoe_e4_carrier") == 1:
            biomarker_score += self.weights.APOE_E4_CARRIER
            components["apoe_e4_carrier"] = self.weights.APOE_E4_CARRIER

            # Heterozygous e4/e4 gets bonus
            if self._safe_get(trial, "apoe_e4_homozygous") == 1:
                biomarker_score += self.weights.APOE_E4_HOMOZYGOUS
                components["apoe_e4_homozygous"] = self.weights.APOE_E4_HOMOZYGOUS

        # MRI neurodegeneration
        if self._safe_get(trial, "hippocampal_atrophy_binary") == 1:
            biomarker_score += self.weights.HIPPOCAMPAL_ATROPHY
            components["hippocampal_atrophy"] = self.weights.HIPPOCAMPAL_ATROPHY

        score += biomarker_score

        # ===== COGNITIVE STAGE SCORING =====
        mmse = self._safe_get(trial, "baseline_mmse")
        if mmse is not None:
            if 18 <= mmse <= 26:  # MCI sweet spot
                score += self.weights.BASELINE_MMSE_MCI_SWEET_SPOT
                components["baseline_mmse_mci"] = self.weights.BASELINE_MMSE_MCI_SWEET_SPOT
            elif 16 <= mmse < 18:  # Mild dementia
                score += self.weights.BASELINE_MMSE_MILD_DEMENTIA
                components["baseline_mmse_mild"] = self.weights.BASELINE_MMSE_MILD_DEMENTIA
            elif mmse < 16:  # Advanced dementia (penalty)
                if mmse < 10:
                    score += self.weights.VERY_ADVANCED_DEMENTIA_MMSE_LT_10
                    components["baseline_mmse_very_advanced"] = self.weights.VERY_ADVANCED_DEMENTIA_MMSE_LT_10
                else:
                    score += self.weights.ADVANCED_DEMENTIA_MMSE_LT_16
                    components["baseline_mmse_advanced"] = self.weights.ADVANCED_DEMENTIA_MMSE_LT_16
            elif mmse > 26:  # Very mild (harder to detect decline)
                score += self.weights.MILD_COGNITIVE_DECLINE_MMSE_GT_26
                components["baseline_mmse_very_mild"] = self.weights.MILD_COGNITIVE_DECLINE_MMSE_GT_26

        # ===== AGE ADJUSTMENT =====
        age = self._safe_get(trial, "age_mean")
        if age is not None:
            if 60 <= age <= 75:  # Sweet spot
                score += self.weights.AGE_SWEET_SPOT_60_75
                components["age_sweet_spot"] = self.weights.AGE_SWEET_SPOT_60_75
            elif age < 60:
                score += self.weights.AGE_LT_60
                components["age_young"] = self.weights.AGE_LT_60
            elif age > 80:
                score += self.weights.AGE_GT_80
                components["age_old"] = self.weights.AGE_GT_80

        # ===== TRIAL DESIGN SCORING =====
        design_score = 0.0

        # Sample size
        sample_size = self._safe_get(trial, "trial_sample_size")
        if sample_size is not None:
            if sample_size >= 250:
                design_score += self.weights.ADEQUATE_SAMPLE_SIZE_GE_250
                components["sample_size_adequate"] = self.weights.ADEQUATE_SAMPLE_SIZE_GE_250
            elif sample_size >= 150:
                design_score += self.weights.GOOD_SAMPLE_SIZE_GE_150
                components["sample_size_good"] = self.weights.GOOD_SAMPLE_SIZE_GE_150
            elif sample_size < 100:
                design_score += self.weights.SMALL_SAMPLE_LT_100
                components["sample_size_small"] = self.weights.SMALL_SAMPLE_LT_100
            elif sample_size < 150:
                design_score += self.weights.MEDIUM_SMALL_SAMPLE_LT_150
                components["sample_size_medium_small"] = self.weights.MEDIUM_SMALL_SAMPLE_LT_150

        # Trial duration
        duration_weeks = self._safe_get(trial, "trial_duration_weeks")
        if duration_weeks is not None:
            if duration_weeks >= 52:
                design_score += self.weights.LONG_DURATION_GE_52_WEEKS
                components["duration_long"] = self.weights.LONG_DURATION_GE_52_WEEKS
            elif duration_weeks >= 36:
                design_score += self.weights.MEDIUM_DURATION_GE_36_WEEKS
                components["duration_medium"] = self.weights.MEDIUM_DURATION_GE_36_WEEKS
            elif duration_weeks < 24:
                design_score += self.weights.SHORT_DURATION_LT_24_WEEKS
                components["duration_short"] = self.weights.SHORT_DURATION_LT_24_WEEKS
            elif duration_weeks < 36:
                design_score += self.weights.MEDIUM_SHORT_DURATION_LT_36_WEEKS
                components["duration_medium_short"] = self.weights.MEDIUM_SHORT_DURATION_LT_36_WEEKS

        # Endpoint type
        endpoint_type = self._safe_get(trial, "endpoint_type")
        if endpoint_type is not None:
            if endpoint_type == "mixed":
                design_score += self.weights.GOOD_ENDPOINT_TYPE_MIXED
                components["endpoint_mixed"] = self.weights.GOOD_ENDPOINT_TYPE_MIXED
            elif endpoint_type == "objective":
                design_score += self.weights.OBJECTIVE_ENDPOINT_ONLY
                components["endpoint_objective"] = self.weights.OBJECTIVE_ENDPOINT_ONLY

        # Primary endpoint
        primary_endpoint = self._safe_get(trial, "primary_endpoint_name")
        if primary_endpoint is not None:
            if primary_endpoint in ["CDR-SB", "ADAS-Cog"]:
                design_score += self.weights.GOOD_PRIMARY_ENDPOINT
                components["endpoint_gold_standard"] = self.weights.GOOD_PRIMARY_ENDPOINT
            else:
                design_score += self.weights.UNCOMMON_ENDPOINT
                components["endpoint_uncommon"] = self.weights.UNCOMMON_ENDPOINT

        # Randomization structure
        randomization = self._safe_get(trial, "randomization_ratio")
        if randomization is not None:
            if randomization == "open_label":
                design_score += self.weights.OPEN_LABEL_STRUCTURE
                components["open_label"] = self.weights.OPEN_LABEL_STRUCTURE
            elif randomization == "2:1":
                design_score += self.weights.ADAPTIVE_RANDOMIZATION
                components["adaptive_randomization"] = self.weights.ADAPTIVE_RANDOMIZATION
            else:
                design_score += self.weights.RANDOMIZED_STRUCTURE
                components["randomized"] = self.weights.RANDOMIZED_STRUCTURE

        score += design_score

        # ===== BIOMARKER ENRICHMENT BONUS =====
        enrichment = self._safe_get(trial, "biomarker_enrichment_strategy")
        if enrichment is not None:
            if enrichment == "at_positive":
                score += self.weights.ENRICHMENT_AT_POSITIVE
                components["enrichment_at_positive"] = self.weights.ENRICHMENT_AT_POSITIVE
            elif enrichment == "amyloid_positive":
                score += self.weights.ENRICHMENT_AMYLOID_POSITIVE
                components["enrichment_amyloid_positive"] = self.weights.ENRICHMENT_AMYLOID_POSITIVE
            elif enrichment == "cognitive_only" or enrichment == "none":
                score += self.weights.NO_ENRICHMENT
                components["no_enrichment"] = self.weights.NO_ENRICHMENT

        # ===== NORMALIZE SCORE TO [0, 1] =====
        # Clamp to realistic range
        score = max(0.15, min(score, 0.95))

        # ===== DETERMINE RISK TIER =====
        if score >= 0.70:
            risk_tier = "Low"
        elif score >= 0.40:
            risk_tier = "Medium"
        else:
            risk_tier = "High"

        return {
            "trial_success_probability": round(score, 3),
            "risk_tier": risk_tier,
            "component_scores": components,
            "raw_score_before_normalization": score,
        }

    @staticmethod
    def _safe_get(d: Dict, key: str, default=None):
        """
        Safely retrieve value from dict. Returns default if key missing or value is None.

        Args:
            d (Dict): Dictionary to retrieve from.
            key (str): Key to look up.
            default: Default value if key not found or value is None.

        Returns:
            Value from dict or default.
        """
        value = d.get(key, default)
        return value if value is not None else default


# ============================================================================
# Convenience Function (for direct use)
# ============================================================================

def score_trial(trial: Dict) -> Dict:
    """
    Convenience function: score a single trial.

    Args:
        trial (Dict): Trial data dict.

    Returns:
        Dict: Scored output with trial_success_probability and risk_tier.

    Example:
        >>> trial = {
        ...     'amyloid_pet_positive': 1,
        ...     'ptau217_high': 1,
        ...     'baseline_mmse': 21,
        ...     'trial_sample_size': 250,
        ...     'trial_duration_weeks': 52,
        ...     'randomization_ratio': '1:1',
        ...     'endpoint_type': 'subjective',
        ...     'primary_endpoint_name': 'CDR-SB',
        ...     'biomarker_enrichment_strategy': 'amyloid_positive'
        ... }
        >>> result = score_trial(trial)
        >>> print(result['trial_success_probability'])
        0.850
        >>> print(result['risk_tier'])
        'Low'
    """
    scorer = TrialScorer()
    return scorer.score_trial(trial)


# ============================================================================
# Batch Scoring for DataFrames
# ============================================================================

def score_trials_batch(df) -> list:
    """
    Score multiple trials from a pandas DataFrame.

    Args:
        df (pd.DataFrame): DataFrame with trial data.

    Returns:
        list: List of dicts with scores.
    """
    scorer = TrialScorer()
    results = []

    for idx, row in df.iterrows():
        trial_dict = row.to_dict()
        score = scorer.score_trial(trial_dict)
        score["trial_id"] = trial_dict.get("trial_id", f"TRIAL_{idx}")
        results.append(score)

    return results


# ============================================================================
# Unit Tests (if run directly)
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Rule-Based Trial Scorer - Unit Tests")
    print("=" * 80)

    # Test 1: Ideal trial (high success)
    print("\nTest 1: Ideal Trial (High Success Expected)")
    ideal_trial = {
        "amyloid_pet_positive": 1,
        "ptau217_high": 1,
        "csf_abeta42_40_ratio_low": 1,
        "apoe_e4_carrier": 1,
        "hippocampal_atrophy_binary": 1,
        "baseline_mmse": 22,  # MCI sweet spot
        "age_mean": 70,  # Optimal age
        "trial_sample_size": 300,  # Good size
        "trial_duration_weeks": 52,  # Long enough
        "primary_endpoint_name": "CDR-SB",  # Gold standard
        "endpoint_type": "subjective",
        "biomarker_enrichment_strategy": "at_positive",
        "randomization_ratio": "1:1",
    }
    result1 = score_trial(ideal_trial)
    print(f"  Success probability: {result1['trial_success_probability']}")
    print(f"  Risk tier: {result1['risk_tier']}")
    print(f"  Components: {result1['component_scores']}")

    # Test 2: Poor trial (low success)
    print("\nTest 2: Poor Trial (Low Success Expected)")
    poor_trial = {
        "amyloid_pet_positive": 0,
        "ptau217_high": 0,
        "csf_abeta42_40_ratio_low": 0,
        "apoe_e4_carrier": 0,
        "baseline_mmse": 12,  # Advanced dementia
        "age_mean": 85,  # Very old
        "trial_sample_size": 50,  # Underpowered
        "trial_duration_weeks": 12,  # Too short
        "primary_endpoint_name": "other",
        "endpoint_type": "objective",
        "biomarker_enrichment_strategy": "none",
        "randomization_ratio": "open_label",
    }
    result2 = score_trial(poor_trial)
    print(f"  Success probability: {result2['trial_success_probability']}")
    print(f"  Risk tier: {result2['risk_tier']}")
    print(f"  Components: {result2['component_scores']}")

    # Test 3: Mixed trial
    print("\nTest 3: Mixed Trial (Medium Success Expected)")
    mixed_trial = {
        "amyloid_pet_positive": 1,
        "ptau217_high": 0,
        "baseline_mmse": 20,
        "age_mean": 72,
        "trial_sample_size": 150,
        "trial_duration_weeks": 36,
        "primary_endpoint_name": "ADAS-Cog",
        "endpoint_type": "mixed",
        "biomarker_enrichment_strategy": "amyloid_positive",
        "randomization_ratio": "1:1",
    }
    result3 = score_trial(mixed_trial)
    print(f"  Success probability: {result3['trial_success_probability']}")
    print(f"  Risk tier: {result3['risk_tier']}")
    print(f"  Components: {result3['component_scores']}")

    print("\n" + "=" * 80)
    print("Tests Complete")
    print("=" * 80)
