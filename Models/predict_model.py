import sys
import os
import torch
from torch.utils.data import DataLoader

# Ensure project root is in sys.path so imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now imports should resolve correctly
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel

class Predictor:
    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initializes the Predictor with a trained model.

        Args:
            model_path (str): Path to the saved model .pt file.
            device (str): 'cpu' or 'cuda' for GPU.
        """
        self.device = torch.device(device)
        self.model = TrialSuccessModel()
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

    def predict(self, data_csv: str, batch_size: int = 32):
        """
        Predict trial outcomes from a CSV file.

        Args:
            data_csv (str): Path to CSV with input data.
            batch_size (int): Number of samples per batch.

        Returns:
            list: Model predictions as a list of numpy arrays.
        """
        dataset = TrialDataset(data_csv)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        predictions = []
        with torch.no_grad():
            for batch in loader:
                inputs = batch.to(self.device)
                outputs = self.model(inputs)
                predictions.extend(outputs.cpu().numpy())
        return predictions