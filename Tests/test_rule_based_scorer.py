import sys
sys.path.insert(0, '.')

import pandas as pd
from models.rule_based_scorer import score_trials_batch

# This test will run scoring over the synthetic processed dataset if available
def test_rule_based_scoring_runs():
    try:
        df = pd.read_csv('data/processed/synthetic_ad_trials.csv')
    except Exception:
        # If data not available, create minimal df
        df = pd.DataFrame({
            'trial_id': [1],
            'trial_success': [1],
        })
    scores = score_trials_batch(df)
    assert isinstance(scores, list)
