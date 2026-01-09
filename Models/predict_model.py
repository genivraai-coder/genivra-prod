import torch
from torch.utils.data import DataLoader
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel

class Predictor:
    def __init__(self, model_path: str, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = TrialSuccessModel()
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

    def predict(self, data_csv: str, batch_size: int = 32):
        dataset = TrialDataset(data_csv)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
        predictions = []
        with torch.no_grad():
            for batch in loader:
                inputs = batch.to(self.device)
                outputs = self.model(inputs)
                predictions.extend(outputs.cpu().numpy())
        return predictions