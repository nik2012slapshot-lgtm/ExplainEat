import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Train a food classification model from explain_eat/training/images.'
    )
    parser.add_argument(
        '--data',
        type=Path,
        default=Path(__file__).resolve().parent.parent / 'explain_eat' / 'training' / 'images',
        help='Path to training images in ImageFolder format.',
    )
    parser.add_argument(
        '--labels',
        type=Path,
        default=Path(__file__).resolve().parent.parent / 'explain_eat' / 'training' / 'food_labels.txt',
        help='Optional label file with one category per line.',
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path(__file__).resolve().parent.parent / 'explain_eat' / 'models' / 'food_classifier.pth',
        help='Output path for the saved model.',
    )
    parser.add_argument(
        '--classes-output',
        type=Path,
        default=Path(__file__).resolve().parent.parent / 'explain_eat' / 'models' / 'food_classes.json',
        help='Output path for the class list.',
    )
    parser.add_argument(
        '--metrics-output',
        type=Path,
        default=Path(__file__).resolve().parent.parent / 'explain_eat' / 'models' / 'metrics.json',
        help='Save evaluation results here.',
    )
    parser.add_argument('--epochs', type=int, default=8, help='Number of training epochs.')
    parser.add_argument('--batch-size', type=int, default=24, help='Batch size for training/validation.')
    parser.add_argument('--img-size', type=int, default=224, help='Image size for the model.')
    parser.add_argument('--val-split', type=float, default=0.15, help='Fraction of validation data.')
    parser.add_argument('--device', type=str, default='cpu', help='Device: cpu or cuda.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility.')
    return parser.parse_args()


def load_class_names(label_path: Path, image_dir: Path) -> List[str]:
    if label_path.exists():
        labels = [line.strip() for line in label_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        if labels:
            return labels

    subdirs = sorted([entry.name for entry in image_dir.iterdir() if entry.is_dir()])
    if not subdirs:
        raise RuntimeError(f'No training data found in {image_dir}.')
    return subdirs


def build_transforms(img_size: int) -> Dict[str, transforms.Compose]:
    return {
        'train': transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
        'val': transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]),
    }


def create_dataloaders(
    image_dir: Path,
    img_size: int,
    batch_size: int,
    val_split: float,
    seed: int,
) -> (DataLoader, DataLoader, List[str]):
    transform = build_transforms(img_size)
    dataset = datasets.ImageFolder(image_dir, transform=transform['train'])
    if len(dataset) == 0:
        raise RuntimeError(f'No images found in the training folder: {image_dir}')

    num_val = max(1, int(len(dataset) * val_split))
    num_train = len(dataset) - num_val
    train_subset, val_subset = torch.utils.data.random_split(
        dataset,
        [num_train, num_val],
        generator=torch.Generator().manual_seed(seed),
    )

    val_dataset = datasets.ImageFolder(image_dir, transform=transform['val'])
    val_subset = Subset(val_dataset, val_subset.indices)

    train_loader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_subset, batch_size=batch_size, shuffle=False, num_workers=0)

    class_names = dataset.classes
    return train_loader, val_loader, class_names


def create_model(num_classes: int, device: torch.device) -> nn.Module:
    try:
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    except Exception:
        model = models.resnet18(pretrained=True)
    for param in model.parameters():
        param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model.to(device)


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)
    return float(correct) / total if total else 0.0


def train(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int,
    device: torch.device,
    metrics_path: Path,
) -> Dict[str, object]:
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=1e-3)

    history = {'train_accuracy': [], 'val_accuracy': []}
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

        train_acc = float(correct) / total if total else 0.0
        val_acc = evaluate(model, val_loader, device)
        history['train_accuracy'].append(train_acc)
        history['val_accuracy'].append(val_acc)

        print(
            f'Epoch {epoch}/{epochs} — loss: {running_loss / max(total, 1):.4f} ' \
            f'— train_acc: {train_acc:.4f} — val_acc: {val_acc:.4f}'
        )

    if metrics_path:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(history, indent=2), encoding='utf-8')

    return history


def save_class_map(class_names: List[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(class_names, indent=2), encoding='utf-8')


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    random.seed(args.seed)

    if not args.data.exists():
        raise FileNotFoundError(f'Training data not found: {args.data}')

    train_loader, val_loader, class_names = create_dataloaders(
        args.data, args.img_size, args.batch_size, args.val_split, args.seed
    )
    device = torch.device(args.device if torch.cuda.is_available() and args.device == 'cuda' else 'cpu')
    model = create_model(len(class_names), device)

    print(f'Starting training on {device} with {len(class_names)} classes.')
    metrics = train(model, train_loader, val_loader, args.epochs, device, args.metrics_output)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.output)
    save_class_map(class_names, args.classes_output)

    summary = {
        'model_path': str(args.output.resolve()),
        'classes_path': str(args.classes_output.resolve()),
        'metrics_path': str(args.metrics_output.resolve()),
        'classes': class_names,
        'train_accuracy': metrics['train_accuracy'][-1] if metrics['train_accuracy'] else 0.0,
        'val_accuracy': metrics['val_accuracy'][-1] if metrics['val_accuracy'] else 0.0,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
