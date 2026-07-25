"""Train ExplainEat's own nutrition AI (a local PyTorch neural network).

Generates a synthetic dataset of (user profile + meal macros) examples, labels
each with a principled nutrition assessment (see ai_model._targets), and trains a
small multi-task MLP to reproduce and generalize those assessments. The result is
a real trained model that drives the app's scores, flags and recommendations —
no external/foundation model involved.

Run:
    python scripts/train_ai_model.py
    python scripts/train_ai_model.py --samples 40000 --epochs 60
"""

import argparse
import random
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from explain_eat.ai_model import (  # noqa: E402
    FLAG_NAMES, RECO_CLASSES, MODEL_PATH, NutritionNet, encode_features, _targets,
)

GOALS = ["health", "muscle", "weight_loss"]
ACTIVITIES = ["low", "moderate", "high"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train ExplainEat's own nutrition AI.")
    p.add_argument("--samples", type=int, default=30000, help="Number of synthetic examples.")
    p.add_argument("--epochs", type=int, default=40, help="Training epochs.")
    p.add_argument("--batch-size", type=int, default=256, help="Batch size.")
    p.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    p.add_argument("--seed", type=int, default=42, help="Random seed.")
    p.add_argument("--output", type=Path, default=MODEL_PATH, help="Where to save the model.")
    return p.parse_args()


def random_example():
    """Samples a plausible (profile, macros) pair."""
    profile = {
        "age": random.randint(16, 80),
        "weight": round(random.uniform(45, 120), 1),
        "activity_level": random.choice(ACTIVITIES),
        "goal": random.choice(GOALS),
    }
    macros = {
        "calories": round(random.uniform(120, 1100), 1),
        "protein_g": round(random.uniform(0, 60), 1),
        "fat_g": round(random.uniform(0, 50), 1),
        "carbs_g": round(random.uniform(0, 130), 1),
        "fiber_g": round(random.uniform(0, 20), 1),
        "sugar_g": round(random.uniform(0, 60), 1),
    }
    return profile, macros


def build_dataset(n: int):
    X, Y_score, Y_flags, Y_reco = [], [], [], []
    for _ in range(n):
        profile, macros = random_example()
        feats = encode_features(profile, macros)
        t = _targets(profile, macros)
        # small label noise on the score so the net learns a smooth boundary
        score = max(0.0, min(1.0, t["score"] + random.uniform(-0.05, 0.05)))
        X.append(feats)
        Y_score.append([score])
        Y_flags.append([1.0 if f else 0.0 for f in t["flags"]])
        Y_reco.append(t["reco"])
    return (
        torch.tensor(X, dtype=torch.float32),
        torch.tensor(Y_score, dtype=torch.float32),
        torch.tensor(Y_flags, dtype=torch.float32),
        torch.tensor(Y_reco, dtype=torch.long),
    )


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    print(f"Generating {args.samples} synthetic training examples...")
    X, Ys, Yf, Yr = build_dataset(args.samples)
    n_val = max(1, int(0.15 * len(X)))
    Xtr, Xval = X[:-n_val], X[-n_val:]
    Ystr, Ysval = Ys[:-n_val], Ys[-n_val:]
    Yftr, Yfval = Yf[:-n_val], Yf[-n_val:]
    Yrtr, Yrval = Yr[:-n_val], Yr[-n_val:]

    model = NutritionNet()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    bce = nn.BCEWithLogitsLoss()
    mse = nn.MSELoss()
    ce = nn.CrossEntropyLoss()
    n_flags = len(FLAG_NAMES)

    n = len(Xtr)
    for epoch in range(1, args.epochs + 1):
        model.train()
        perm = torch.randperm(n)
        total = 0.0
        for i in range(0, n, args.batch_size):
            idx = perm[i:i + args.batch_size]
            out = model(Xtr[idx])
            score_logit = out[:, 0:1]
            flag_logits = out[:, 1:1 + n_flags]
            reco_logits = out[:, 1 + n_flags:]
            loss = (
                mse(torch.sigmoid(score_logit), Ystr[idx])
                + bce(flag_logits, Yftr[idx])
                + ce(reco_logits, Yrtr[idx])
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total += loss.item() * len(idx)

        if epoch % 5 == 0 or epoch == args.epochs:
            model.eval()
            with torch.no_grad():
                out = model(Xval)
                reco_acc = (out[:, 1 + n_flags:].argmax(1) == Yrval).float().mean().item()
                flag_pred = (torch.sigmoid(out[:, 1:1 + n_flags]) > 0.5).float()
                flag_acc = (flag_pred == Yfval).float().mean().item()
                score_mae = (torch.sigmoid(out[:, 0:1]) - Ysval).abs().mean().item()
            print(f"Epoch {epoch:3d}/{args.epochs} — loss {total / n:.4f} | "
                  f"reco_acc {reco_acc:.3f} | flag_acc {flag_acc:.3f} | score_mae {score_mae:.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), args.output)
    print(f"\nSaved ExplainEat AI model to {args.output}")
    print("Recommendation classes:", RECO_CLASSES)
    print("The backend loads it automatically on the next start.")


if __name__ == "__main__":
    main()
