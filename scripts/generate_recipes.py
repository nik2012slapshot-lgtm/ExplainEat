"""Generate a large, diverse set of valid recipes for ExplainEat.

Produces recipes with REAL ingredient names that resolve in the nutrition
database (so the AI scores them correctly), sensible portions, steps and tags.
Keeps the user's own (non-placeholder) recipes and tops up to --target total.

Run:
    python scripts/generate_recipes.py --target 1000
"""

import argparse
import json
import random
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RECIPES_PATH = ROOT / "explain_eat" / "recipes.json"

# (display name, grams) — display names all resolve via nutrition.lookup_nutrition
PROTEINS = [
    "Grilled Chicken", "Chicken Breast", "Beef", "Lean Beef", "Salmon", "Tuna",
    "Shrimp", "Tofu", "Turkey", "Egg", "Pork", "White Fish", "Black Beans",
    "Chickpeas", "Ham", "Lamb",
]
CARBS = [
    "Rice", "Brown Rice", "Quinoa", "Pasta", "Whole Wheat Pasta", "Potatoes",
    "Sweet Potato", "Bread",
]
VEGS = [
    "Broccoli", "Carrot", "Cherry Tomatoes", "Tomato", "Cucumber", "Spinach",
    "Lettuce", "Onion", "Corn",
]
EXTRAS = [("Avocado", 30), ("Olive Oil", 10), ("Cheese", 30), ("Greek Yogurt", 60)]
ADJECTIVES = [
    "Grilled", "Roasted", "Spicy", "Herb", "Garlic", "Lemon", "Teriyaki",
    "Mediterranean", "Asian", "Zesty", "Smoky", "Classic", "Fresh", "Hearty",
    "Protein-Packed", "Sesame", "Honey", "Pesto", "Cajun", "Sweet Chili",
]
STYLES = ["Bowl", "Stir Fry", "Salad", "Plate", "Skillet", "Bake", "Wrap",
          "Curry", "Power Bowl", "Protein Bowl", "Meal Prep"]
VEGETARIAN = {"Tofu", "Egg", "Black Beans", "Chickpeas"}

PLACEHOLDER_INGREDIENTS = {
    "protein source", "whole grain", "vegetable", "vegetable 1", "vegetable 2",
}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def is_placeholder(recipe: dict) -> bool:
    name = str(recipe.get("name", ""))
    if re.match(r"^Healthy .+ Recipe \d+$", name):
        return True
    for ing in recipe.get("ingredients", []):
        if str(ing.get("name", "")).strip().lower() in PLACEHOLDER_INGREDIENTS:
            return True
    return False


def make_steps(protein: str, carb: str, vegs: list, style: str) -> list:
    veg_text = " and ".join(v.lower() for v in vegs) if vegs else "the vegetables"
    base = [
        f"Cook the {carb.lower()} according to the package instructions.",
        f"Season the {protein.lower()} and cook until done.",
        f"Prepare {veg_text}.",
    ]
    finish = {
        "Stir Fry": "Toss everything in a hot pan for 3-4 minutes and serve.",
        "Salad": "Combine everything raw, add dressing and toss well.",
        "Bake": "Combine in an oven dish and bake at 200 °C for 15 minutes.",
        "Curry": "Simmer everything in sauce for 10 minutes and serve with the carb.",
        "Wrap": "Wrap everything in a flatbread and serve.",
    }.get(style, "Combine everything in a bowl, season to taste and serve.")
    base.append(finish)
    return base


def make_recipe(used_names: set) -> dict:
    for _ in range(50):
        protein = random.choice(PROTEINS)
        carb = random.choice(CARBS)
        vegs = random.sample(VEGS, k=random.choice([1, 2, 2, 3]))
        style = random.choice(STYLES)
        adj = random.choice(ADJECTIVES)
        show_carb = random.random() < 0.5
        name = (f"{adj} {protein} & {carb} {style}" if show_carb
                else f"{adj} {protein} {style}")
        if name.lower() not in used_names:
            break
    used_names.add(name.lower())

    ingredients = [
        {"name": protein, "grams": random.choice([140, 150, 160, 170, 180])},
        {"name": carb, "grams": random.choice([70, 80, 90, 100, 110])},
    ]
    for v in vegs:
        ingredients.append({"name": v, "grams": random.choice([80, 90, 100, 110, 120])})
    if random.random() < 0.55:
        ex_name, ex_g = random.choice(EXTRAS)
        ingredients.append({"name": ex_name, "grams": ex_g})

    tags = ["high-protein", style.lower().replace(" ", "-")]
    if protein in VEGETARIAN:
        tags.append("vegetarian")

    return {
        "id": slugify(name),
        "name": name,
        "description": f"A tasty {style.lower()} with {protein.lower()} and {carb.lower()}.",
        "base_servings": 1,
        "tags": tags,
        "ingredients": ingredients,
        "steps": make_steps(protein, carb, vegs, style),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=1000, help="Total recipe count.")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    random.seed(args.seed)

    current = []
    if RECIPES_PATH.exists():
        try:
            data = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
            # flatten one level defensively
            for entry in data:
                for r in (entry if isinstance(entry, list) else [entry]):
                    if isinstance(r, dict) and "id" in r and isinstance(r.get("ingredients"), list):
                        current.append(r)
        except Exception as e:
            print(f"Could not read existing recipes: {e}")

    # keep the user's real recipes, drop placeholders AND duplicate names
    kept = []
    seen_ids = set()
    used_names = set()  # lowercased names, for dedupe
    for r in current:
        if is_placeholder(r):
            continue
        name_key = str(r.get("name", "")).strip().lower()
        rid = str(r.get("id"))
        if name_key in used_names or rid in seen_ids:
            continue
        used_names.add(name_key)
        seen_ids.add(rid)
        kept.append(r)
    print(f"Kept {len(kept)} unique recipes "
          f"(removed {len(current) - len(kept)} placeholders/duplicates).")

    generated = 0
    while len(kept) < args.target:
        r = make_recipe(used_names)
        if r["id"] in seen_ids:
            r["id"] = f"{r['id']}-{len(kept)}"
        seen_ids.add(r["id"])
        kept.append(r)
        generated += 1

    if RECIPES_PATH.exists():
        shutil.copy(RECIPES_PATH, RECIPES_PATH.with_suffix(".backup3.json"))
    RECIPES_PATH.write_text(json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(kept)} recipes to {RECIPES_PATH} ({generated} newly generated).")
    print(f"Backup: {RECIPES_PATH.with_suffix('.backup3.json').name}")


if __name__ == "__main__":
    main()
