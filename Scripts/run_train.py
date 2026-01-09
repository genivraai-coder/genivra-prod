import argparse
import os
import torch
from torch.utils.data import DataLoader, random_split
from features.build_features import TrialDataset
from models.trial_success_model import TrialSuccessModel
from evaluation.metrics import calculate_metrics
from evaluation.plots import plot_training_curve

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    for inputs, targets in loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs.squeeze(), targets.float())
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
    return running_loss / len(loader.dataset)

def eval_epoch(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_targets = []
    all_preds = []
    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs.squeeze(), targets.float())
            running_loss += loss.item() * inputs.size(0)
            all_targets.extend(targets.cpu().numpy())
            all_preds.extend(outputs.squeeze().cpu().numpy())
    metrics = calculate_metrics(all_targets, all_preds)
    return running_loss / len(loader.dataset), metrics

def main(
    data_path,
    model_path,
    output_dir,
    batch_size=16,
    lr=1e-3,
    epochs=20,
    test_split=0.2,
    device=None
):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    dataset = TrialDataset(data_path)
    test_size = int(len(dataset) * test_split)
    train_size = len(dataset) - test_size
    train_set, test_set = random_split(dataset, [train_size, test_size])

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

    model = TrialSuccessModel().to(device)
    criterion = torch.nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    train_losses = []
    val_losses = []

    for epoch in range(1, epochs + 1):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, metrics = eval_epoch(model, test_loader, criterion, device)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        print(
            f"Epoch {epoch}/{epochs} - Train Loss: {train_loss:.4f} "
            f"- Val Loss: {val_loss:.4f} - Metrics: {metrics}"
        )

    os.makedirs(output_dir, exist_ok=True)
    torch.save(model.state_dict(), os.path.join(output_dir, model_path))
    plot_training_curve(train_losses, val_losses, os.path.join(output_dir, "training_curve.png"))
    print(f"Model and training curve saved to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Trial Success Model")
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--model_path", type=str, default="checkpoint.pt")
    parser.add_argument("--output_dir", type=str, default="outputs")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--test_split", type=float, default=0.2)
    parser.add_argument("--device", type=str, default=None)

    args = parser.parse_args()
    main(
        args.data_path,
        args.model_path,
        args.output_dir,
        args.batch_size,
        args.lr,
        args.epochs,
        args.test_split,
        args.device,
    )