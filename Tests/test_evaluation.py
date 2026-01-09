import argparse
import os
import torch
from torch.utils.data import DataLoader
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel
from evaluation.metrics import calculate_metrics
from evaluation.plots import plot_training_curve

def evaluate_model(model_path, data_path, batch_size=16, device=None, output_dir="outputs"):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    dataset = TrialDataset(data_path)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    model = TrialSuccessModel().to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    all_targets = []
    all_preds = []

    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            all_targets.extend(targets.cpu().numpy())
            all_preds.extend(outputs.squeeze().cpu().numpy())

    metrics = calculate_metrics(all_targets, all_preds)
    print("Evaluation Metrics:", metrics)

    os.makedirs(output_dir, exist_ok=True)
    metrics_path = os.path.join(output_dir, "evaluation_metrics.txt")
    with open(metrics_path, "w") as f:
        for key, value in metrics.items():
            f.write(f"{key}: {value}\n")
    print(f"Metrics saved to {metrics_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Trained Trial Success Model")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--output_dir", type=str, default="outputs")

    args = parser.parse_args()
    evaluate_model(
        args.model_path,
        args.data_path,
        args.batch_size,
        args.device,
        args.output_dir
    )