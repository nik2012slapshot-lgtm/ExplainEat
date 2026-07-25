"""Train a YOLO object-detection model for ExplainEat.

Detects multiple foods per photo (with position/box), unlike the
single-label classifier in train_classifier.py.

Requirement:
    pip install ultralytics

Dataset (YOLO format):
    explain_eat/training/yolo/
        data.yaml
        images/train/*.jpg   + labels/train/*.txt
        images/val/*.jpg     + labels/val/*.txt

Each label file (.txt) has one line per object:
    <class_id> <x_center> <y_center> <width> <height>   (all normalized 0..1)

Example call:
    python scripts/train_yolo.py --epochs 80 --img-size 640
    python scripts/train_yolo.py --device 0          # GPU
"""

import argparse
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "explain_eat" / "training" / "yolo"
DATA_YAML = DATA_DIR / "data.yaml"
MODEL_OUT = ROOT / "explain_eat" / "models" / "food_detector.pt"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train a YOLO food detector.")
    p.add_argument("--data", type=Path, default=DATA_YAML, help="Path to data.yaml.")
    p.add_argument("--base-model", type=str, default="yolo11n.pt",
                   help="Pretrained base model (yolo11n=small/fast, yolo11s/m=more accurate).")
    p.add_argument("--epochs", type=int, default=80, help="Number of training epochs.")
    p.add_argument("--img-size", type=int, default=640, help="Image size.")
    p.add_argument("--batch-size", type=int, default=8, help="Batch size.")
    p.add_argument("--device", type=str, default="cpu", help="cpu or GPU index, e.g. 0.")
    p.add_argument("--patience", type=int, default=20, help="Early-stopping patience.")
    p.add_argument("--output", type=Path, default=MODEL_OUT, help="Target path for the best model.")
    return p.parse_args()


def write_resolved_yaml(data_path: Path) -> Path:
    """Writes a temporary data.yaml with an absolute 'path' so YOLO can find it."""
    cfg = yaml.safe_load(data_path.read_text(encoding="utf-8"))
    cfg["path"] = str(data_path.parent.resolve())
    resolved = data_path.parent / "_data_resolved.yaml"
    resolved.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    return resolved


def count_dataset(data_path: Path) -> None:
    base = data_path.parent
    for split in ("train", "val"):
        imgs = list((base / "images" / split).glob("*.*"))
        lbls = list((base / "labels" / split).glob("*.txt"))
        print(f"  {split}: {len(imgs)} images, {len(lbls)} label files")
        if split == "train" and not imgs:
            raise RuntimeError(
                f"No training images in {base/'images'/split}. "
                "Add images + matching .txt labels (see README_YOLO.md)."
            )


def main() -> None:
    args = parse_args()

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise SystemExit(
            "ultralytics is not installed. Please run:\n"
            "    pip install ultralytics\n"
            f"(original error: {e})"
        )

    if not args.data.exists():
        raise FileNotFoundError(f"data.yaml not found: {args.data}")

    print(f"Dataset under {args.data.parent}:")
    count_dataset(args.data)

    resolved_yaml = write_resolved_yaml(args.data)

    print(f"\nStarting YOLO training: base={args.base_model}, epochs={args.epochs}, "
          f"img={args.img_size}, device={args.device}")
    model = YOLO(args.base_model)
    results = model.train(
        data=str(resolved_yaml),
        epochs=args.epochs,
        imgsz=args.img_size,
        batch=args.batch_size,
        device=args.device,
        patience=args.patience,
        project=str(ROOT / "explain_eat" / "training" / "yolo_runs"),
        name="food_detector",
        exist_ok=True,
    )

    # copy the best weights to a fixed path so yolo_vision.py can find it
    best = Path(results.save_dir) / "weights" / "best.pt"
    if best.exists():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best, args.output)
        print(f"\nBest model copied to: {args.output}")
    else:
        print(f"\nWarning: best.pt not found at {best}")

    print("Done. The model is loaded automatically on the next backend start.")


if __name__ == "__main__":
    main()
