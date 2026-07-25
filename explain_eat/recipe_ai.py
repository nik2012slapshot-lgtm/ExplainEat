"""ExplainEat AI recipe generator.

Creates a NEW recipe tailored to one user. It starts from an existing recipe as
inspiration (the "given recipes"), then composes real ingredients and computes
portions so the meal hits the user's per-meal protein and calorie targets, avoids
their allergies, and scores well with the trained nutrition model (ai_model).

This is part of ExplainEat's own AI — it uses the locally trained neural network
to evaluate and pick the best candidate, not an external/foundation model.
"""

import random
import time
from typing import Any, Dict, List, Optional

from . import ai_model
from .allergens import ingredient_conflicts, recipe_conflicts
from .nutrition import NUTRITION_DATABASE
from .recipes import load_recipes

# Ingredient pools (all must exist in NUTRITION_DATABASE so macros are real).
PROTEINS_BY_GOAL = {
    "muscle": ["chicken", "salmon", "tuna", "egg", "beef", "turkey", "shrimp", "tofu", "fish"],
    "weight_loss": ["chicken", "tuna", "tofu", "shrimp", "fish", "turkey", "egg"],
    "health": ["chicken", "salmon", "tofu", "egg", "beans", "fish", "turkey"],
}
ALL_PROTEINS = ["chicken", "beef", "pork", "salmon", "egg", "shrimp", "tuna", "tofu",
                "turkey", "ham", "cheese", "fish", "lamb", "beans"]
CARBS = ["rice", "potatoes", "pasta", "bread"]
VEGS = ["broccoli", "spinach", "carrot", "tomato", "cucumber", "lettuce", "onion", "corn"]
FATS = ["avocado"]


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _allowed(name: str, allergies: List[str]) -> bool:
    return not ingredient_conflicts(name, allergies)


def _parse_allergies(profile: Dict[str, Any]) -> List[str]:
    allergies = profile.get("allergies") or []
    if isinstance(allergies, str):
        allergies = [a.strip() for a in allergies.split(",") if a.strip()]
    return [a for a in allergies if a]


def _cal(name: str, grams: float) -> float:
    return NUTRITION_DATABASE.get(name, {}).get("calories", 0.0) * grams / 100.0


def _classify(name: str) -> Optional[str]:
    n = name.lower()
    if n in ALL_PROTEINS:
        return "protein"
    if n in CARBS:
        return "carb"
    if n in VEGS:
        return "veg"
    if n in FATS:
        return "fat"
    return None


def pick_inspiration() -> Optional[Dict[str, Any]]:
    """Picks a recipe whose ingredients use known foods, to inspire generation."""
    real = []
    for r in load_recipes():
        names = [str(i.get("name", "")).lower() for i in r.get("ingredients", [])]
        if any(_classify(n) for n in names):
            real.append(r)
    return random.choice(real) if real else None


def _components_from_base(base: Optional[Dict[str, Any]], allergies: List[str]):
    """Extracts a protein, carb and vegetables from a base recipe (allergy-safe)."""
    protein = carb = None
    vegs: List[str] = []
    if base:
        for ing in base.get("ingredients", []):
            name = str(ing.get("name", "")).lower()
            kind = _classify(name)
            if not _allowed(name, allergies):
                continue
            if kind == "protein" and protein is None:
                protein = name
            elif kind == "carb" and carb is None:
                carb = name
            elif kind == "veg" and len(vegs) < 2:
                vegs.append(name)
    return protein, carb, vegs


def _has_allergen(recipe: Dict[str, Any], allergies: List[str]) -> bool:
    return recipe_conflicts(recipe, allergies)


def suggest_recipes(profile: Dict[str, Any], limit: int = 12) -> List[Dict[str, Any]]:
    """Ranks all recipes for this user with the trained model; returns the best.

    Skips recipes containing the user's allergens, scores every remaining recipe
    with ai_model.predict for THIS profile, and returns the top `limit` sorted by
    the AI's meal-fit score.
    """
    allergies = _parse_allergies(profile)
    scored = []
    for recipe in load_recipes():
        if _has_allergen(recipe, allergies):
            continue
        macros = ai_model._sum_macros_from_items(recipe.get("ingredients", []))
        pred = ai_model.predict(profile, macros)
        scored.append((pred["score"], recipe, pred))

    scored.sort(key=lambda x: x[0], reverse=True)
    suggestions = []
    seen_names = set()
    for score, recipe, pred in scored:
        name_key = str(recipe.get("name", "")).strip().lower()
        if name_key in seen_names:
            continue  # keep suggestions distinct
        seen_names.add(name_key)
        item = dict(recipe)
        item["score"] = round(score * 100)
        item["recommendation"] = pred["recommendation"]
        suggestions.append(item)
        if len(suggestions) >= limit:
            break
    return suggestions


def generate_personalized_recipe(
    profile: Dict[str, Any], base: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Builds and scores a personalized recipe for the user."""
    allergies = _parse_allergies(profile)
    goal = str(profile.get("goal", "health")).lower()
    targets = ai_model.meal_targets(profile)

    # Start from the inspiration recipe, fill any gaps from the goal-based pools.
    protein, carb, vegs = _components_from_base(base, allergies)

    if protein is None:
        pref = [p for p in PROTEINS_BY_GOAL.get(goal, PROTEINS_BY_GOAL["health"]) if _allowed(p, allergies)]
        protein = random.choice(pref) if pref else "tofu"
    if carb is None:
        carb_pool = [c for c in CARBS if _allowed(c, allergies)]
        carb = random.choice(carb_pool) if carb_pool else "rice"
    if not vegs:
        veg_pool = [v for v in VEGS if _allowed(v, allergies)]
        random.shuffle(veg_pool)
        vegs = veg_pool[:2] if veg_pool else []

    # Protein grams to meet the user's per-meal protein need.
    p_per_100 = NUTRITION_DATABASE.get(protein, {}).get("protein_g", 0) or 20.0
    g_protein = _clamp(round(targets["protein_need_meal"] * 100 / p_per_100), 80, 320)

    g_veg = 110
    fat = "avocado" if (_allowed("avocado", allergies) and goal != "weight_loss") else None
    g_fat = 30

    used = _cal(protein, g_protein) + sum(_cal(v, g_veg) for v in vegs) + (_cal(fat, g_fat) if fat else 0)
    remaining = max(0.0, targets["calorie_target_meal"] - used)
    c_per_100 = NUTRITION_DATABASE.get(carb, {}).get("calories", 0) or 130.0
    g_carb = _clamp(round(remaining * 100 / c_per_100), 40, 320)

    ingredients = [
        {"name": protein.title(), "grams": g_protein},
        {"name": carb.title(), "grams": g_carb},
    ]
    ingredients += [{"name": v.title(), "grams": g_veg} for v in vegs]
    if fat:
        ingredients.append({"name": fat.title(), "grams": g_fat})

    # Evaluate with the trained model; if fiber is flagged low, add one more veg.
    macros = ai_model._sum_macros_from_items(ingredients)
    pred = ai_model.predict(profile, macros)
    if pred["flags"].get("fiber_low"):
        extra = [v for v in VEGS if _allowed(v, allergies) and v not in vegs]
        if extra:
            ingredients.append({"name": random.choice(extra).title(), "grams": g_veg})
            macros = ai_model._sum_macros_from_items(ingredients)
            pred = ai_model.predict(profile, macros)

    steps = [
        f"Cook the {carb} until done.",
        f"Season and cook the {protein} until cooked through.",
        f"Prepare the vegetables ({', '.join(vegs) if vegs else 'of your choice'}).",
        "Combine everything in a bowl, season to taste and serve.",
    ]

    recipe = {
        "id": f"ai-{int(time.time())}-{random.randint(100, 999)}",
        "name": f"AI {protein.title()} & {carb.title()} Bowl",
        "description": f"Auto-generated by ExplainEat AI to fit your {goal} goal and body weight.",
        "base_servings": 1,
        "tags": ["ai-generated", goal],
        "generated": True,
        "score": round(pred["score"] * 100),
        "ingredients": ingredients,
        "steps": steps,
    }
    if base:
        recipe["based_on"] = base.get("name")
    return recipe
