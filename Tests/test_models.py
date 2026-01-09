import unittest
import os
import torch
from models.train_models import train_model
from models.predict_models import predict_model
from features.build_features import build_features, TrialDataset
from torch.utils.data import DataLoader

class TestModels(unittest.TestCase):
    def setUp(self):
        # Create a small sample dataset
        self.test_csv = os.path.join(os.path.dirname(__file__), "sample_trials.csv")
        if not os.path.exists(self.test_csv):
            import pandas as pd
            df = pd.DataFrame({
                "trial_id": [1, 2, 3, 4],
                "indication": ["Alzheimer's", "ALS", "Alzheimer's", "ALS"],
                "biomarker_1": [0.5, 0.7, 0.6, 0.8],
                "biomarker_2": [1.2, 0.8, 1.1, 0.9],
                "outcome": [1, 0, 1, 0]
            })
            df.to_csv(self.test_csv, index=False)
        
        self.features_df = build_features(self.test_csv)
        self.dataset = TrialDataset(self.test_csv)
        self.dataloader = DataLoader(self.dataset, batch_size=2)

    def test_training_runs(self):
        model, loss_val = train_model(self.dataloader, epochs=2, lr=0.01)
        self.assertIsInstance(model, torch.nn.Module)
        self.assertGreaterEqual(loss_val, 0)

    def test_prediction_output(self):
        model, _ = train_model(self.dataloader, epochs=2, lr=0.01)
        preds = predict_model(model, self.dataloader)
        self.assertEqual(len(preds), len(self.dataset))
        self.assertTrue(all(p in [0, 1] for p in preds.tolist()))

    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

if __name__ == "__main__":
    unittest.main()