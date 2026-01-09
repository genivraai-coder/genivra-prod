import torch
from torch.utils.data import DataLoader
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel
from evaluation.metrics import compute_metrics
from evaluation.plots import plot_confusion_matrix, plot_roc_curve
import argparse
import os

def main(data_path, model_path, batch_size=16, device=None):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    # Load dataset
    dataset = TrialDataset(data_path)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    # Load model
    model = TrialSuccessModel().to(device)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # Evaluate
    all_preds, all_targets = [], []
    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            all_preds.extend(outputs.squeeze().cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

    # Compute metrics
    metrics = compute_metrics(all_targets, all_preds)
    print("Evaluation Metrics:")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    # Plots
    plot_confusion_matrix(all_targets, all_preds, threshold=0.5)
    plot_roc_curve(all_targets, all_preds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Trial Success Model")
    parser.add_argument("--data_path", type=str, required=True, help="Path to CSV dataset")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained model checkpoint")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--device", type=str, default=None, help="cuda or cpu")

    args = parser.parse_args()
    main(args.data_path, args.model_path, args.batch_size, args.device)