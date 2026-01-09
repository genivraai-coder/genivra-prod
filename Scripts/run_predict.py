import torch
from torch.utils.data import DataLoader
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel
import pandas as pd
import argparse
import os

def main(input_path, model_path, output_path, batch_size=16, device=None):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    # Load dataset
    dataset = TrialDataset(input_path, predict_only=True)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    # Load model
    model = TrialSuccessModel().to(device)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model checkpoint not found at {model_path}")
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    # Make predictions
    predictions = []
    trial_ids = []

    with torch.no_grad():
        for inputs, ids in loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            predictions.extend(outputs.squeeze().cpu().numpy())
            trial_ids.extend(ids)

    # Save predictions to CSV
    df = pd.DataFrame({"trial_id": trial_ids, "predicted_success_prob": predictions})
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict Trial Success Probabilities")
    parser.add_argument("--input_path", type=str, required=True, help="Path to input CSV dataset")
    parser.add_argument("--model_path", type=str, required=True, help="Path to trained model checkpoint")
    parser.add_argument("--output_path", type=str, required=True, help="Path to save predictions CSV")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--device", type=str, default=None, help="cuda or cpu")

    args = parser.parse_args()
    main(args.input_path, args.model_path, args.output_path, args.batch_size, args.device)