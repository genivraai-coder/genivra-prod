import unittest
import os
import pandas as pd
from features.build_features import build_features, TrialDataset

class TestFeaturePipeline(unittest.TestCase):
    def setUp(self):
        # Use a small sample dataset for testing
        self.test_csv = os.path.join(os.path.dirname(__file__), "sample_trials.csv")
        # Create a small dummy dataset
        if not os.path.exists(self.test_csv):
            df = pd.DataFrame({
                "trial_id": [1, 2],
                "indication": ["Alzheimer's", "ALS"],
                "biomarker_1": [0.5, 0.7],
                "biomarker_2": [1.2, 0.8],
                "outcome": [1, 0]
            })
            df.to_csv(self.test_csv, index=False)

    def test_build_features_output(self):
        features_df = build_features(self.test_csv)
        self.assertIsInstance(features_df, pd.DataFrame)
        self.assertIn("trial_id", features_df.columns)
        self.assertIn("outcome", features_df.columns)
        self.assertGreater(features_df.shape[0], 0)

    def test_dataset_class(self):
        dataset = TrialDataset(self.test_csv)
        self.assertEqual(len(dataset), 2)
        sample_input, sample_target = dataset[0]
        self.assertEqual(sample_input.shape[0], len(dataset.feature_cols))
        self.assertIn(sample_target.item(), [0, 1])

    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

if __name__ == "__main__":
    unittest.main()