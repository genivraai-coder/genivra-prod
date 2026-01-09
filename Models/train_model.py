
import torch
from torch.utils.data import DataLoader, random_split
from torch import nn, optim
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel
from evaluation.metrics import compute_metrics

class Trainer:
    def __init__(self, data_csv: str, model_path: str = "models/checkpoint.pt", device: str = "cpu"):
        self.device = torch.device(device)
        self.model = TrialSuccessModel().to(self.device)
        self.model_path = model_path
        self.dataset = TrialDataset(data_csv)

    def train(self, epochs: int = 20, batch_size: int = 32, lr: float = 1e-3, val_split: float = 0.2):
        val_size = int(len(self.dataset) * val_split)
        train_size = len(self.dataset) - val_size
        train_dataset, val_dataset = random_split(self.dataset, [train_size, val_size])

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=lr)

        for epoch in range(1, epochs + 1):
            self.model.train()
            running_loss = 0.0
            for batch in train_loader:
                inputs, targets = batch
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs.squeeze(), targets.float())
                loss.backward()
                optimizer.step()
                running_loss += loss.item() * inputs.size(0)

            train_loss = running_loss / train_size

            val_loss, val_metrics = self.evaluate(val_loader)
            print(f"Epoch {epoch}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Metrics: {val_metrics}")

            torch.save(self.model.state_dict(), self.model_path)

    def evaluate(self, loader):
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []

        criterion = nn.BCELoss()
        with torch.no_grad():
            for batch in loader:
                inputs, targets = batch
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = self.model(inputs)
                loss = criterion(outputs.squeeze(), targets.float())
                total_loss += loss.item() * inputs.size(0)
                all_preds.extend(outputs.squeeze().cpu().numpy())
                all_targets.extend(targets.cpu().numpy())

        avg_loss = total_loss / len(loader.dataset)
        metrics = compute_metrics(all_targets, all_preds)
        return avg_loss, metrics