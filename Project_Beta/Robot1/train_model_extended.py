# train_model_extended.py
# Extended Training script with automatic logging and iteration management
# Based on original train_model.py with added features for iteration tracking

import argparse
import json
import os
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import yaml

# Import model from same directory
from model import DrivingNetwork


class DrivingDataset(Dataset):
    """
    Dataset for driving imitation learning.

    Loads image + SOC as input, drive_torque + steer_angle as targets.
    Only uses data AFTER the start signal (excludes StartSequence).
    """

    def __init__(self, data_dirs, transform=None, exclude_start_sequence=True):
        """
        Args:
            data_dirs: List of paths to data directories (each containing metadata.csv and images/)
            transform: Image transforms to apply
            exclude_start_sequence: If True, skip StartSequence data (recommended)
        """
        self.samples = []
        self.transform = transform

        # Handle single directory or list
        if isinstance(data_dirs, (str, Path)):
            data_dirs = [data_dirs]

        for data_dir in data_dirs:
            data_dir = Path(data_dir)
            csv_path = data_dir / "metadata.csv"

            if not csv_path.exists():
                print(f"[Warning] metadata.csv not found in {data_dir}, skipping...")
                continue

            df = pd.read_csv(csv_path)
            images_dir = data_dir / "images"

            loaded_count = 0
            skipped_start = 0
            for _, row in df.iterrows():
                # Skip StartSequence data (before race start)
                if exclude_start_sequence and row.get("status") == "StartSequence":
                    skipped_start += 1
                    continue

                img_path = images_dir / row["filename"]

                if not img_path.exists():
                    continue

                self.samples.append({
                    "image_path": str(img_path),
                    "soc": float(row["soc"]),
                    "drive_torque": float(row["drive_torque"]),
                    "steer_angle": float(row["steer_angle"]),
                })
                loaded_count += 1

            if skipped_start > 0:
                print(f"[Dataset] Loaded {loaded_count} samples from {data_dir.name} (skipped {skipped_start} StartSequence)")
            else:
                print(f"[Dataset] Loaded {loaded_count} samples from {data_dir.name}")

        print(f"[Dataset] Total samples: {len(self.samples)}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # Load image
        image = Image.open(sample["image_path"]).convert("RGB")

        if self.transform:
            image = self.transform(image)

        # SOC as tensor
        soc = torch.tensor([sample["soc"]], dtype=torch.float32)

        # Targets: [drive_torque, steer_angle]
        targets = torch.tensor([
            sample["drive_torque"],
            sample["steer_angle"]
        ], dtype=torch.float32)

        return {
            "image": image,
            "soc": soc,
            "targets": targets
        }


def get_data_transforms():
    """Get image transforms for training and validation."""
    # Training transforms (with augmentation)
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])

    # Validation transforms (no augmentation)
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])

    return train_transform, val_transform


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    total_torque_loss = 0.0
    total_steer_loss = 0.0

    for batch in dataloader:
        images = batch["image"].to(device)
        soc = batch["soc"].to(device)
        targets = batch["targets"].to(device)

        optimizer.zero_grad()

        # Forward pass
        outputs = model(images, soc)

        # Compute loss
        loss = criterion(outputs, targets)

        # Backward pass
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        # Individual losses for logging
        with torch.no_grad():
            torque_loss = nn.MSELoss()(outputs[:, 0], targets[:, 0])
            steer_loss = nn.MSELoss()(outputs[:, 1], targets[:, 1])
            total_torque_loss += torque_loss.item()
            total_steer_loss += steer_loss.item()

    n_batches = len(dataloader)
    return {
        "loss": total_loss / n_batches,
        "torque_loss": total_torque_loss / n_batches,
        "steer_loss": total_steer_loss / n_batches
    }


def validate(model, dataloader, criterion, device):
    """Validate the model."""
    model.eval()
    total_loss = 0.0
    total_torque_loss = 0.0
    total_steer_loss = 0.0

    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(device)
            soc = batch["soc"].to(device)
            targets = batch["targets"].to(device)

            outputs = model(images, soc)
            loss = criterion(outputs, targets)

            total_loss += loss.item()

            torque_loss = nn.MSELoss()(outputs[:, 0], targets[:, 0])
            steer_loss = nn.MSELoss()(outputs[:, 1], targets[:, 1])
            total_torque_loss += torque_loss.item()
            total_steer_loss += steer_loss.item()

    n_batches = len(dataloader)
    return {
        "loss": total_loss / n_batches,
        "torque_loss": total_torque_loss / n_batches,
        "steer_loss": total_steer_loss / n_batches
    }


def find_data_directories(base_path):
    """Find all run_* directories containing training data."""
    base_path = Path(base_path)
    data_dirs = []

    for d in sorted(base_path.iterdir()):
        if d.is_dir() and d.name.startswith("run_"):
            csv_path = d / "metadata.csv"
            if csv_path.exists():
                data_dirs.append(d)

    return data_dirs


def plot_loss_curve(train_losses, val_losses, save_path):
    """
    Plot and save training/validation loss curve.

    Args:
        train_losses: List of training losses per epoch
        val_losses: List of validation losses per epoch
        save_path: Path to save the plot
    """
    plt.figure(figsize=(12, 6))

    epochs = range(1, len(train_losses) + 1)

    plt.plot(epochs, train_losses, 'b-', label='Train Loss', linewidth=2)
    plt.plot(epochs, val_losses, 'r-', label='Val Loss', linewidth=2)

    # Mark best validation loss
    best_val_idx = val_losses.index(min(val_losses))
    plt.scatter([best_val_idx + 1], [val_losses[best_val_idx]],
                color='red', s=100, zorder=5, label=f'Best Val Loss (Epoch {best_val_idx + 1})')

    plt.xlabel('Epoch', fontsize=12)
    plt.ylabel('Loss (MSE)', fontsize=12)
    plt.title('Training and Validation Loss Curve', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(save_path, dpi=150)
    plt.close()

    print(f"[Train] Loss curve saved to: {save_path}")


def save_training_info(args, train_losses, val_losses, best_epoch, best_val_loss,
                      model, data_dirs, train_size, val_size, output_dir, device, training_time):
    """
    Save comprehensive training information to markdown file.

    Args:
        args: Command line arguments
        train_losses: List of training losses
        val_losses: List of validation losses
        best_epoch: Epoch with best validation loss
        best_val_loss: Best validation loss value
        model: Trained model
        data_dirs: List of data directories used
        train_size: Number of training samples
        val_size: Number of validation samples
        output_dir: Output directory path
        device: Device used for training
        training_time: Total training time in seconds
    """
    output_dir = Path(output_dir)

    # Model architecture string
    model_arch = str(model)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    # Calculate overfitting ratio
    overfit_ratio = val_losses[-1] / train_losses[-1] if train_losses[-1] > 0 else 1.0

    # Create training_info.md
    info_md = f"""# Training Info - {output_dir.name}

**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## データソース

### 使用したrun
"""

    for data_dir in data_dirs:
        info_md += f"- {data_dir.name}\n"

    info_md += f"""
（合計: {len(data_dirs)} runs, {train_size + val_size:,} フレーム）

### データ統計
- 総フレーム数: {train_size + val_size:,}
- Training: {train_size:,} ({train_size/(train_size+val_size)*100:.1f}%)
- Validation: {val_size:,} ({val_size/(train_size+val_size)*100:.1f}%)

## モデルアーキテクチャ

```
{model_arch}
```

### パラメータ数
- Total parameters: {total_params:,}
- Trainable parameters: {trainable_params:,}
- Model size: {total_params * 4 / (1024**2):.2f} MB (FP32)

## 学習設定

- **エポック数:** {args.epochs}
- **バッチサイズ:** {args.batch_size}
- **学習率:** {args.lr}
- **Optimizer:** AdamW (weight_decay=1e-4)
- **Loss Function:** MSE
- **Scheduler:** ReduceLROnPlateau (factor=0.5, patience=10)
- **Device:** {device}
- **Train/Val Split:** {(1-args.val_split)*100:.0f}/{args.val_split*100:.0f}

## 学習結果

- **最終Train Loss:** {train_losses[-1]:.6f}
- **最終Val Loss:** {val_losses[-1]:.6f}
- **最良Val Loss:** {best_val_loss:.6f} (epoch {best_epoch + 1})
- **学習時間:** {training_time//3600:.0f}h {(training_time%3600)//60:.0f}m {training_time%60:.0f}s
- **過学習チェック:** Val/Train比 = {overfit_ratio:.3f} {'✅ 正常' if overfit_ratio < 1.3 else '⚠️ 過学習の可能性'}

### Loss詳細（最終エポック）

| 指標 | Train | Val |
|-----|-------|-----|
| Total Loss | {train_losses[-1]:.6f} | {val_losses[-1]:.6f} |

### Loss推移グラフ

![Loss Curve](logs/loss_curve.png)

## 評価結果（3回走行）

| Run | 完走 | 時間(s) | クラッシュ地点 | 原因 |
|-----|------|---------|--------------|------|
| 1   | -    | -       | -            | (未実施) |
| 2   | -    | -       | -            | (未実施) |
| 3   | -    | -       | -            | (未実施) |

**完走率:** - (テスト走行後に更新)

## 次のステップ

1. ✅ 学習完了
2. ⏳ テスト走行（3回）を実施
3. ⏳ 完走率を評価
4. ⏳ クラッシュ分析（必要な場合）

## 備考

（ここにメモや気づきを追記）

---
**生成日時:** {datetime.now().isoformat()}
"""

    info_path = output_dir / "training_info.md"
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(info_md)

    print(f"[Train] Training info saved to: {info_path}")

    # Also save as JSON for programmatic access
    training_data = {
        "timestamp": datetime.now().isoformat(),
        "data_sources": [str(d) for d in data_dirs],
        "model": {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
        },
        "training": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "learning_rate": args.lr,
            "device": str(device),
            "training_time_sec": training_time,
        },
        "results": {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "best_epoch": best_epoch + 1,
            "best_val_loss": best_val_loss,
            "final_train_loss": train_losses[-1],
            "final_val_loss": val_losses[-1],
            "overfit_ratio": overfit_ratio,
        },
        "samples": {
            "total": train_size + val_size,
            "train": train_size,
            "val": val_size,
        }
    }

    json_path = output_dir / "logs" / "training_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(training_data, f, indent=2)

    print(f"[Train] Training results (JSON) saved to: {json_path}")


def update_training_config(output_dir, best_val_loss, best_epoch):
    """
    Update training_config.yaml with training results.

    Args:
        output_dir: Output directory path
        best_val_loss: Best validation loss
        best_epoch: Best epoch number
    """
    config_path = Path(output_dir) / "training_config.yaml"

    if not config_path.exists():
        print(f"[Warning] training_config.yaml not found at {config_path}")
        return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Update training section
        config["training"]["status"] = "completed"
        config["training"]["completed_at"] = datetime.now().isoformat()
        config["training"]["model_path"] = "model.pth"
        config["training"]["best_val_loss"] = float(best_val_loss)
        config["training"]["best_epoch"] = int(best_epoch + 1)

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

        print(f"[Train] Updated training_config.yaml")
    except Exception as e:
        print(f"[Warning] Could not update training_config.yaml: {e}")
        print(f"[Info] Training results are still saved in training_info.md and training_results.json")


def main():
    parser = argparse.ArgumentParser(description="Train End-to-End Driving Model (Extended)")
    parser.add_argument("--data", type=str, required=True,
                        help="Path to training data directory (contains run_* folders)")
    parser.add_argument("--output", type=str, required=True,
                        help="Output directory (iteration folder)")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4,
                        help="Learning rate")
    parser.add_argument("--val-split", type=float, default=0.2,
                        help="Validation split ratio")
    parser.add_argument("--device", type=str, default="auto",
                        help="Device to use (cuda/cpu/auto)")

    args = parser.parse_args()

    start_time = datetime.now()

    # Setup device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    print(f"[Train] Using device: {device}")

    # Setup output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create logs directory
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Find data directories
    data_base = script_dir / args.data

    data_dirs = find_data_directories(data_base)
    if not data_dirs:
        print(f"[Error] No training data found in {data_base}")
        print("Expected structure: training_data/run_YYYYMMDD_HHMMSS/metadata.csv")
        return

    print(f"[Train] Found {len(data_dirs)} data directories:")
    for d in data_dirs:
        print(f"  - {d.name}")

    # Create dataset
    train_transform, val_transform = get_data_transforms()

    # Use train transform for full dataset (will split later)
    full_dataset = DrivingDataset(data_dirs, transform=train_transform)

    if len(full_dataset) == 0:
        print("[Error] No samples loaded. Check your data.")
        return

    # Split into train/val
    val_size = int(len(full_dataset) * args.val_split)
    train_size = len(full_dataset) - val_size

    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    print(f"[Train] Training samples: {train_size}")
    print(f"[Train] Validation samples: {val_size}")

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,  # Windows compatibility
        pin_memory=True if device.type == "cuda" else False
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True if device.type == "cuda" else False
    )

    # Create model
    model = DrivingNetwork().to(device)
    print(f"[Train] Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=10
    )

    # Training loop
    best_val_loss = float('inf')
    best_epoch = 0
    train_losses = []
    val_losses = []

    model_path = output_dir / "model.pth"
    log_path = logs_dir / "training_log.txt"

    # Open log file
    log_file = open(log_path, 'w', encoding='utf-8')
    log_file.write(f"Training Log - {datetime.now().isoformat()}\n")
    log_file.write("=" * 80 + "\n\n")

    print(f"\n[Train] Starting training for {args.epochs} epochs...")
    print("=" * 80)

    for epoch in range(args.epochs):
        # Train
        train_metrics = train_one_epoch(model, train_loader, criterion, optimizer, device)
        train_losses.append(train_metrics["loss"])

        # Validate
        val_metrics = validate(model, val_loader, criterion, device)
        val_losses.append(val_metrics["loss"])

        # Update scheduler
        scheduler.step(val_metrics["loss"])

        # Save best model
        if val_metrics["loss"] < best_val_loss:
            best_val_loss = val_metrics["loss"]
            best_epoch = epoch
            torch.save(model.state_dict(), model_path)
            save_marker = " [SAVED]"
        else:
            save_marker = ""

        # Print progress
        log_line = (f"Epoch {epoch+1:3d}/{args.epochs} | "
                   f"Train Loss: {train_metrics['loss']:.6f} "
                   f"(T:{train_metrics['torque_loss']:.4f}, S:{train_metrics['steer_loss']:.4f}) | "
                   f"Val Loss: {val_metrics['loss']:.6f} "
                   f"(T:{val_metrics['torque_loss']:.4f}, S:{val_metrics['steer_loss']:.4f})"
                   f"{save_marker}")

        print(log_line)
        log_file.write(log_line + "\n")
        log_file.flush()

    log_file.close()

    print("=" * 80)
    print(f"[Train] Training complete!")
    print(f"[Train] Best validation loss: {best_val_loss:.6f} (epoch {best_epoch + 1})")
    print(f"[Train] Model saved to: {model_path}")

    # Calculate training time
    end_time = datetime.now()
    training_time = (end_time - start_time).total_seconds()

    # Plot loss curve
    print(f"\n[Train] Generating loss curve...")
    plot_loss_curve(train_losses, val_losses, logs_dir / "loss_curve.png")

    # Save training info
    print(f"\n[Train] Saving training info...")
    save_training_info(
        args, train_losses, val_losses, best_epoch, best_val_loss,
        model, data_dirs, train_size, val_size, output_dir, device, training_time
    )

    # Update training_config.yaml if it exists
    update_training_config(output_dir, best_val_loss, best_epoch)

    print(f"\n{'='*80}")
    print(f"✅ All training artifacts saved to: {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
