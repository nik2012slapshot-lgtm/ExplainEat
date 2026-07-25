"""ExplainEat's own AI — a locally trained neural network.

This is a self-built nutrition model (PyTorch), NOT an external/foundation LLM.
It takes the user's profile plus the meal's macros and predicts:

  * a meal-quality score for the user's goal (0..1),
  * binary flags (protein low, fiber low, sugar high, calorie mismatch),
  * a recommendation class (add protein / vegetables / complex carbs / balanced).

Train it with: python scripts/train_ai_model.py
The weights are saved to explain_eat/models/nutrition_ai.pt.

The natural-language tips are composed from the network's predictions (templates),
because training a local language generator is out of scope — but the *decisions*
come from the trained model, not from hand-written rules. If no trained model is
present, a transparent heuristic fallback keeps the app working.
"""

import random
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except Exception:  # pragma: no cover
    torch = None
    nn = None
    HAS_TORCH = False

MODEL_PATH = Path(__file__).parent / "models" / "nutrition_ai.pt"

FLAG_NAMES = ["protein_low", "fiber_low", "sugar_high", "calorie_mismatch"]
RECO_CLASSES = ["add_protein", "add_vegetables", "add_complex_carbs", "balanced"]

INPUT_DIM = 12          # see encode_features
OUTPUT_DIM = 1 + len(FLAG_NAMES) + len(RECO_CLASSES)  # score + flags + reco logits

_GOALS = ["health", "muscle", "weight_loss"]
_ACTIVITY = {"low": 0.0, "moderate": 0.5, "high": 1.0}


def encode_features(profile: Dict[str, Any], macros: Dict[str, Any]) -> List[float]:
    """Turns a profile + meal macros into the network's 12-dim input vector.

    Kept identical between training and inference so the model sees the same shape.
    """
    def num(d, key, default=0.0):
        try:
            return float(d.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    age = num(profile, "age", 30)
    weight = num(profile, "weight", 70)
    activity = _ACTIVITY.get(
        str(profile.get("activity_level", profile.get("activity", "moderate"))).lower(), 0.5
    )
    goal = str(profile.get("goal", "health")).lower()
    goal_oh = [1.0 if goal == g else 0.0 for g in _GOALS]

    calories = num(macros, "calories")
    protein = num(macros, "protein_g")
    fat = num(macros, "fat_g")
    carbs = num(macros, "carbs_g")
    fiber = num(macros, "fiber_g")
    sugar = num(macros, "sugar_g")

    return [
        age / 100.0,
        weight / 150.0,
        activity,
        *goal_oh,
        calories / 1000.0,
        protein / 100.0,
        fat / 100.0,
        carbs / 150.0,
        fiber / 50.0,
        sugar / 100.0,
    ]


if HAS_TORCH:
    class NutritionNet(nn.Module):
        """Small multi-task MLP: shared trunk → score + flags + recommendation."""

        def __init__(self, input_dim: int = INPUT_DIM, output_dim: int = OUTPUT_DIM):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, output_dim),
            )

        def forward(self, x):
            return self.net(x)
else:  # pragma: no cover
    NutritionNet = None


_model: Optional["NutritionNet"] = None
_tried_load = False


def _load_model() -> Optional["NutritionNet"]:
    global _model, _tried_load
    if _tried_load:
        return _model
    _tried_load = True
    if not HAS_TORCH or not MODEL_PATH.exists():
        if not MODEL_PATH.exists():
            print(f"Note: no trained AI model at {MODEL_PATH} — "
                  "run scripts/train_ai_model.py (using heuristic fallback meanwhile).")
        return None
    try:
        model = NutritionNet()
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        model.eval()
        _model = model
        print("ExplainEat AI model loaded.")
    except Exception as e:
        print(f"Error loading AI model: {e}")
        _model = None
    return _model


def is_ready() -> bool:
    """True if the own trained neural network is loaded and used for predictions."""
    return _load_model() is not None


# --- Heuristic fallback (also the source of training targets) -----------------

def meal_targets(profile: Dict[str, Any]) -> Dict[str, float]:
    """Per-meal protein and calorie targets derived from the user's profile."""
    def num(d, k, dv=0.0):
        try:
            return float(d.get(k, dv))
        except (TypeError, ValueError):
            return dv

    weight = num(profile, "weight", 70)
    goal = str(profile.get("goal", "health")).lower()
    activity = str(profile.get("activity_level", profile.get("activity", "moderate"))).lower()

    protein_per_kg = {"muscle": 1.6, "weight_loss": 1.4}.get(goal, 1.0)
    activity_mult = {"low": 1.3, "moderate": 1.5, "high": 1.7}.get(activity, 1.5)
    goal_mult = {"muscle": 1.1, "weight_loss": 0.85}.get(goal, 1.0)

    return {
        "protein_need_meal": weight * protein_per_kg / 3.0,
        "calorie_target_meal": weight * 24 * activity_mult * goal_mult / 3.0,
    }


def _targets(profile: Dict[str, Any], macros: Dict[str, Any]) -> Dict[str, Any]:
    """Principled nutrition assessment. Used as training labels and as fallback."""
    def num(d, k, dv=0.0):
        try:
            return float(d.get(k, dv))
        except (TypeError, ValueError):
            return dv

    goal = str(profile.get("goal", "health")).lower()
    calories = num(macros, "calories")
    protein = num(macros, "protein_g")
    fiber = num(macros, "fiber_g")
    sugar = num(macros, "sugar_g")

    targets = meal_targets(profile)
    protein_need_meal = targets["protein_need_meal"]
    calorie_target_meal = targets["calorie_target_meal"]

    protein_low = protein < 0.8 * protein_need_meal
    fiber_low = fiber < (10.0 if goal in ("weight_loss", "health") else 8.0)
    sugar_high = sugar > (12.0 if goal == "weight_loss" else 20.0)
    calorie_mismatch = (
        calorie_target_meal > 0 and abs(calories - calorie_target_meal) / calorie_target_meal > 0.4
    )

    penalties = (0.25 * protein_low + 0.15 * fiber_low + 0.20 * sugar_high + 0.20 * calorie_mismatch)
    score = max(0.0, min(1.0, 1.0 - penalties))

    if protein_low:
        reco = 0
    elif fiber_low or sugar_high:
        reco = 1
    elif calories < 0.6 * calorie_target_meal:
        reco = 2
    else:
        reco = 3

    return {
        "score": score,
        "flags": [protein_low, fiber_low, sugar_high, calorie_mismatch],
        "reco": reco,
        "calorie_target_meal": calorie_target_meal,
    }


def predict(profile: Dict[str, Any], macros: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the trained network (or heuristic fallback) on one profile+meal."""
    model = _load_model()
    if model is None:
        t = _targets(profile, macros)
        return {
            "score": round(t["score"], 3),
            "flags": {n: bool(v) for n, v in zip(FLAG_NAMES, t["flags"])},
            "recommendation": RECO_CLASSES[t["reco"]],
            "confidence": 1.0,
            "source": "heuristic",
        }

    feats = encode_features(profile, macros)
    with torch.no_grad():
        out = model(torch.tensor([feats], dtype=torch.float32))[0]
    score = torch.sigmoid(out[0]).item()
    flags = {n: torch.sigmoid(out[1 + i]).item() > 0.5 for i, n in enumerate(FLAG_NAMES)}
    reco_logits = out[1 + len(FLAG_NAMES):]
    probs = torch.softmax(reco_logits, dim=0)
    reco_idx = int(torch.argmax(probs))
    return {
        "score": round(score, 3),
        "flags": flags,
        "recommendation": RECO_CLASSES[reco_idx],
        "confidence": round(probs[reco_idx].item(), 3),
        "source": "model",
    }


# --- Natural-language presentation of the model's decisions -------------------

_RECO_TEXT = {
    "add_protein": "Add a lean protein source (chicken, fish, tofu, eggs or legumes).",
    "add_vegetables": "Add more vegetables or a fruit for fiber and micronutrients.",
    "add_complex_carbs": "Add complex carbs (rice, oats, potatoes or whole-grain bread) for energy.",
    "balanced": "This meal is well balanced for your goal — keep it up.",
}


def _score_sentence(score: float, goal: str) -> str:
    goal_label = {"muscle": "muscle-building", "weight_loss": "weight-loss"}.get(goal, "health")
    if score >= 0.75:
        opts = [
            f"Great match for your {goal_label} goal ({round(score * 100)}/100).",
            f"This meal scores {round(score * 100)}/100 for your {goal_label} goal — well done.",
        ]
    elif score >= 0.5:
        opts = [
            f"Decent for your {goal_label} goal ({round(score * 100)}/100), with room to improve.",
            f"A reasonable choice ({round(score * 100)}/100) — a small tweak would help.",
        ]
    else:
        opts = [
            f"Not yet aligned with your {goal_label} goal ({round(score * 100)}/100).",
            f"This meal scores low ({round(score * 100)}/100) for your {goal_label} goal.",
        ]
    return random.choice(opts)


def generate_meal_explanation(
    nutrition_report: Dict[str, Any], profile: Dict[str, Any]
) -> Optional[List[str]]:
    """Personalized tips composed from the trained model's predictions."""
    macros = nutrition_report.get("macros", {})
    pred = predict(profile, macros)
    goal = str(profile.get("goal", "health")).lower()

    tips: List[str] = [_score_sentence(pred["score"], goal)]
    flags = pred["flags"]
    if flags.get("protein_low"):
        tips.append("Protein is a bit low for your body weight and goal.")
    if flags.get("fiber_low"):
        tips.append("Fiber is low — more vegetables or whole grains would help digestion.")
    if flags.get("sugar_high"):
        tips.append("Sugar is on the high side, which can cause energy swings.")
    if flags.get("calorie_mismatch"):
        tips.append("The calorie amount doesn't match your estimated needs for this meal.")
    tips.append(_RECO_TEXT.get(pred["recommendation"], _RECO_TEXT["balanced"]))
    return tips


def _sum_macros_from_items(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """Estimates a recipe's macros from its ingredients via the nutrition DB."""
    from .nutrition import lookup_nutrition
    totals = {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0}
    for it in items:
        grams = float(it.get("grams", 0) or 0)
        data = lookup_nutrition(str(it.get("name", "")))
        factor = grams / 100.0
        for k in totals:
            totals[k] += data.get(k, 0.0) * factor
    return totals


def generate_shopping_advice(
    shopping_list: Dict[str, Any], profile: Dict[str, Any]
) -> Optional[str]:
    """Recipe shopping advice driven by the model's assessment of the recipe macros."""
    items = shopping_list.get("items", [])
    macros = _sum_macros_from_items(items)
    pred = predict(profile, {
        # per-meal view of the whole recipe
        "calories": macros["calories"], "protein_g": macros["protein_g"],
        "fat_g": macros["fat_g"], "carbs_g": macros["carbs_g"],
        "fiber_g": macros["fiber_g"], "sugar_g": macros["sugar_g"],
    })
    goal = str(profile.get("goal", "health")).lower()
    scale = shopping_list.get("scale_factor", 1.0)

    parts = [
        f"These amounts are scaled to your body weight, activity and {goal} goal (×{scale}).",
        _score_sentence(pred["score"], goal),
    ]
    if pred["recommendation"] != "balanced":
        parts.append(_RECO_TEXT[pred["recommendation"]])
    # allergy awareness
    if any(it.get("allergy_warning") for it in items):
        parts.append("Heads up: one or more ingredients match your allergies — substitute them.")
    return " ".join(parts)
