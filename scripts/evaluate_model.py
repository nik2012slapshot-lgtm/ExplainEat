"""Misst das trainierte Modell und vergleicht es mit einfachen Baselines.

Erzeugt die Zahlen fuer Anhang B der Dokumentation. Der Testanteil wird
strikt getrennt gehalten und erst am Schluss verwendet.

    python scripts/evaluate_model.py --samples 30000 --seed 42
"""
import argparse
import hashlib
import platform
import subprocess
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from explain_eat.ai_model import (  # noqa: E402
    FLAG_NAMES, RECO_CLASSES, MODEL_PATH, NutritionNet,
)
from scripts.train_ai_model import build_dataset  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--samples", type=int, default=30000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--tolerance", type=float, default=5.0,
                   help="Toleranz in Score-Punkten (0-100) fuer die Toleranzquote.")
    return p.parse_args()


def file_hash(path: Path) -> str:
    if not path.exists():
        return "nicht vorhanden"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "nicht verfuegbar"


def regression_metrics(pred, true):
    """pred/true auf der 0-100-Skala."""
    err = pred - true
    abs_err = err.abs()
    mae = abs_err.mean().item()
    rmse = (err ** 2).mean().sqrt().item()
    ss_res = (err ** 2).sum().item()
    ss_tot = ((true - true.mean()) ** 2).sum().item()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return mae, rmse, r2, abs_err


def main():
    args = parse_args()
    torch.manual_seed(args.seed)

    print(f"Erzeuge {args.samples} Beispiele (seed {args.seed}) ...")
    import random
    random.seed(args.seed)
    X, Ys, Yf, Yr = build_dataset(args.samples)

    # 70 / 15 / 15 — Test bleibt bis zum Schluss unberuehrt
    n = len(X)
    n_test = int(0.15 * n)
    n_val = int(0.15 * n)
    n_train = n - n_val - n_test
    Xtr, Xval, Xte = X[:n_train], X[n_train:n_train + n_val], X[n_train + n_val:]
    Ytr, Yval, Yte = Ys[:n_train], Ys[n_train:n_train + n_val], Ys[n_train + n_val:]
    Yrte = Yr[n_train + n_val:]
    Yfte = Yf[n_train + n_val:]

    print(f"Split: train {n_train} / val {n_val} / test {n_test}")

    if not MODEL_PATH.exists():
        print(f"\nKein Modell unter {MODEL_PATH}. Zuerst scripts/train_ai_model.py laufen lassen.")
        sys.exit(1)

    model = NutritionNet()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    n_flags = len(FLAG_NAMES)
    with torch.no_grad():
        out = model(Xte)
        score_pred = torch.sigmoid(out[:, 0:1]) * 100.0
        reco_acc = (out[:, 1 + n_flags:].argmax(1) == Yrte).float().mean().item()
        flag_pred = (torch.sigmoid(out[:, 1:1 + n_flags]) > 0.5).float()
        flag_acc = (flag_pred == Yfte).float().mean().item()

    score_true = Yte * 100.0
    mae, rmse, r2, abs_err = regression_metrics(score_pred, score_true)
    tol_rate = (abs_err <= args.tolerance).float().mean().item()
    p95 = abs_err.flatten().kthvalue(max(1, int(0.95 * abs_err.numel()))).values.item()
    max_err = abs_err.max().item()

    # Baseline 1: Mittelwert des Trainingsanteils
    const_pred = torch.full_like(score_true, (Ytr * 100.0).mean().item())
    b_mae, b_rmse, b_r2, _ = regression_metrics(const_pred, score_true)

    # Baseline 2: lineare Regression (kleinste Quadrate) auf denselben Features
    A = torch.cat([Xtr, torch.ones(len(Xtr), 1)], dim=1)
    coef = torch.linalg.lstsq(A, Ytr * 100.0).solution
    Ate = torch.cat([Xte, torch.ones(len(Xte), 1)], dim=1)
    lin_pred = Ate @ coef
    l_mae, l_rmse, l_r2, _ = regression_metrics(lin_pred, score_true)

    print("\n" + "=" * 62)
    print("ERGEBNISSE AUF DEM UNABHAENGIGEN TESTANTEIL")
    print("=" * 62)
    print(f"  Score MAE                 {mae:.2f} Punkte (0-100)")
    print(f"  Score RMSE                {rmse:.2f}")
    print(f"  Score R^2                 {r2:.3f}")
    print(f"  Toleranzquote (+-{args.tolerance:.0f} Pkt) {tol_rate*100:.1f} %")
    print(f"  95. Perzentil Fehler      {p95:.2f}")
    print(f"  Maximalfehler             {max_err:.2f}")
    print(f"  Empfehlungsklasse Acc     {reco_acc*100:.1f} %")
    print(f"  Flag-Genauigkeit          {flag_acc*100:.1f} %")
    print("-" * 62)
    print("BASELINES (gleicher Testanteil)")
    print(f"  Konstante (Mittelwert)    MAE {b_mae:.2f} | RMSE {b_rmse:.2f} | R^2 {b_r2:.3f}")
    print(f"  Lineare Regression        MAE {l_mae:.2f} | RMSE {l_rmse:.2f} | R^2 {l_r2:.3f}")
    print(f"  Regel-Engine              MAE 0.00 — erzeugt die Zielwerte selbst")
    print("=" * 62)

    print("\nAnhang-B-Werte:\n")
    rows = [
        ("Git-Commit", git_commit()),
        ("Python-Version", platform.python_version()),
        ("PyTorch-Version", torch.__version__),
        ("Anzahl Beispiele", f"{n}"),
        ("Train / Validation / Test", f"{n_train} / {n_val} / {n_test} (70 / 15 / 15 %)"),
        ("Random Seed", f"{args.seed}"),
        ("Anzahl Features", f"{X.shape[1]}"),
        ("MAE (Test)", f"{mae:.2f} Punkte"),
        ("RMSE (Test)", f"{rmse:.2f}"),
        ("R² (Test)", f"{r2:.3f}"),
        ("Toleranzquote", f"±{args.tolerance:.0f} Punkte: {tol_rate*100:.1f} %"),
        ("Maximalfehler / 95. Perzentil", f"{max_err:.2f} / {p95:.2f}"),
        ("Empfehlungsklasse (Accuracy)", f"{reco_acc*100:.1f} %"),
        ("Flag-Genauigkeit", f"{flag_acc*100:.1f} %"),
        ("Lineare Baseline", f"MAE {l_mae:.2f} | R² {l_r2:.3f}"),
        ("Konstante Baseline", f"MAE {b_mae:.2f} | R² {b_r2:.3f}"),
        ("Modellartefakt (SHA-256, 16)", file_hash(MODEL_PATH)),
    ]
    for k, v in rows:
        print(f"| {k} | {v} |")


if __name__ == "__main__":
    main()
