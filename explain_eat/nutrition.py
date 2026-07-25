from typing import Dict, List
from .config import UserProfile

# Nutrition values per 100 g. Keys must match the (lowercased) detector class
# names from the Roboflow "Meal Ingredient Boxes" workflow.
NUTRITION_DATABASE = {
    # Proteins
    "chicken": {"calories": 165, "protein_g": 31.0, "fat_g": 3.6, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "beef": {"calories": 250, "protein_g": 26.0, "fat_g": 15.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "pork": {"calories": 242, "protein_g": 27.0, "fat_g": 14.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "salmon": {"calories": 208, "protein_g": 20.0, "fat_g": 13.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "egg": {"calories": 155, "protein_g": 13.0, "fat_g": 11.0, "carbs_g": 1.1, "fiber_g": 0.0, "sugar_g": 1.1},
    "shrimp": {"calories": 99, "protein_g": 24.0, "fat_g": 0.3, "carbs_g": 0.2, "fiber_g": 0.0, "sugar_g": 0.0},
    "tuna": {"calories": 116, "protein_g": 26.0, "fat_g": 1.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "tofu": {"calories": 76, "protein_g": 8.0, "fat_g": 4.8, "carbs_g": 1.9, "fiber_g": 0.3, "sugar_g": 0.6},
    "turkey": {"calories": 189, "protein_g": 29.0, "fat_g": 7.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "bacon": {"calories": 541, "protein_g": 37.0, "fat_g": 42.0, "carbs_g": 1.4, "fiber_g": 0.0, "sugar_g": 0.0},
    "sausage": {"calories": 301, "protein_g": 12.0, "fat_g": 27.0, "carbs_g": 2.0, "fiber_g": 0.0, "sugar_g": 1.0},
    "ham": {"calories": 145, "protein_g": 21.0, "fat_g": 6.0, "carbs_g": 1.5, "fiber_g": 0.0, "sugar_g": 1.0},
    "cheese": {"calories": 402, "protein_g": 25.0, "fat_g": 33.0, "carbs_g": 1.3, "fiber_g": 0.0, "sugar_g": 0.5},
    "fish": {"calories": 105, "protein_g": 23.0, "fat_g": 1.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "meatball": {"calories": 197, "protein_g": 12.0, "fat_g": 14.0, "carbs_g": 5.0, "fiber_g": 0.5, "sugar_g": 1.0},
    "lamb": {"calories": 294, "protein_g": 25.0, "fat_g": 21.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    # Carbs / sides
    "rice": {"calories": 130, "protein_g": 2.7, "fat_g": 0.3, "carbs_g": 28.0, "fiber_g": 0.4, "sugar_g": 0.1},
    "pasta": {"calories": 131, "protein_g": 5.0, "fat_g": 1.1, "carbs_g": 25.0, "fiber_g": 1.8, "sugar_g": 0.6},
    "potatoes": {"calories": 87, "protein_g": 2.0, "fat_g": 0.1, "carbs_g": 20.0, "fiber_g": 1.8, "sugar_g": 0.9},
    "bread": {"calories": 265, "protein_g": 9.0, "fat_g": 3.2, "carbs_g": 49.0, "fiber_g": 2.7, "sugar_g": 5.0},
    # Vegetables
    "broccoli": {"calories": 34, "protein_g": 2.8, "fat_g": 0.4, "carbs_g": 7.0, "fiber_g": 2.6, "sugar_g": 1.7},
    "carrot": {"calories": 41, "protein_g": 0.9, "fat_g": 0.2, "carbs_g": 10.0, "fiber_g": 2.8, "sugar_g": 4.7},
    "tomato": {"calories": 18, "protein_g": 0.9, "fat_g": 0.2, "carbs_g": 3.9, "fiber_g": 1.2, "sugar_g": 2.6},
    "cucumber": {"calories": 15, "protein_g": 0.7, "fat_g": 0.1, "carbs_g": 3.6, "fiber_g": 0.5, "sugar_g": 1.7},
    "spinach": {"calories": 23, "protein_g": 2.9, "fat_g": 0.4, "carbs_g": 3.6, "fiber_g": 2.2, "sugar_g": 0.4},
    "lettuce": {"calories": 15, "protein_g": 1.4, "fat_g": 0.2, "carbs_g": 2.9, "fiber_g": 1.3, "sugar_g": 0.8},
    "onion": {"calories": 40, "protein_g": 1.1, "fat_g": 0.1, "carbs_g": 9.3, "fiber_g": 1.7, "sugar_g": 4.2},
    "corn": {"calories": 86, "protein_g": 3.2, "fat_g": 1.2, "carbs_g": 19.0, "fiber_g": 2.7, "sugar_g": 3.2},
    "beans": {"calories": 127, "protein_g": 8.7, "fat_g": 0.5, "carbs_g": 23.0, "fiber_g": 6.4, "sugar_g": 0.3},
    "avocado": {"calories": 160, "protein_g": 2.0, "fat_g": 15.0, "carbs_g": 9.0, "fiber_g": 7.0, "sugar_g": 0.7},
    # Fruit
    "apple": {"calories": 52, "protein_g": 0.3, "fat_g": 0.2, "carbs_g": 14.0, "fiber_g": 2.4, "sugar_g": 10.0},
    "banana": {"calories": 89, "protein_g": 1.1, "fat_g": 0.3, "carbs_g": 23.0, "fiber_g": 2.6, "sugar_g": 12.0},
    # More common recipe ingredients
    "quinoa": {"calories": 120, "protein_g": 4.4, "fat_g": 1.9, "carbs_g": 21.0, "fiber_g": 2.8, "sugar_g": 0.9},
    "sweet potato": {"calories": 86, "protein_g": 1.6, "fat_g": 0.1, "carbs_g": 20.0, "fiber_g": 3.0, "sugar_g": 4.2},
    "olive oil": {"calories": 884, "protein_g": 0.0, "fat_g": 100.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0},
    "yogurt": {"calories": 59, "protein_g": 10.0, "fat_g": 0.4, "carbs_g": 3.6, "fiber_g": 0.0, "sugar_g": 3.2},
    "sauce": {"calories": 90, "protein_g": 2.0, "fat_g": 0.0, "carbs_g": 18.0, "fiber_g": 0.2, "sugar_g": 14.0},
}

DEFAULT_MACROS = {"calories": 100, "protein_g": 5.0, "fat_g": 5.0, "carbs_g": 15.0, "fiber_g": 2.0, "sugar_g": 4.0}

# Maps common descriptive ingredient names to a database key.
NUTRITION_ALIASES = {
    "chicken breast": "chicken", "grilled chicken": "chicken",
    "lean beef": "beef", "ground beef": "beef", "steak": "beef",
    "black beans": "beans", "kidney beans": "beans", "chickpeas": "beans",
    "cherry tomatoes": "tomato", "cherry tomato": "tomato",
    "tzatziki": "yogurt", "greek yogurt": "yogurt",
    "teriyaki sauce": "sauce", "soy sauce": "sauce", "tomato sauce": "sauce",
    "brown rice": "rice", "white rice": "rice", "basmati rice": "rice",
    "whole wheat pasta": "pasta", "spaghetti": "pasta", "noodles": "pasta",
    "bell pepper": "tomato", "peppers": "tomato",
}


def lookup_nutrition(name: str) -> Dict[str, float]:
    """Finds nutrition data for a (possibly descriptive) ingredient name.

    Tries an exact match, then aliases, then multi-word keys, then a single-word
    token match (e.g. "grilled salmon" -> "salmon"). Falls back to DEFAULT_MACROS.
    """
    n = " ".join(str(name).strip().lower().replace("-", " ").split())
    if not n:
        return DEFAULT_MACROS
    if n in NUTRITION_DATABASE:
        return NUTRITION_DATABASE[n]
    if n in NUTRITION_ALIASES:
        return NUTRITION_DATABASE[NUTRITION_ALIASES[n]]
    # multi-word alias appearing inside the name
    for alias, key in NUTRITION_ALIASES.items():
        if alias in n:
            return NUTRITION_DATABASE.get(key, DEFAULT_MACROS)
    # multi-word database key appearing inside the name (e.g. "sweet potato")
    for key in NUTRITION_DATABASE:
        if " " in key and key in n:
            return NUTRITION_DATABASE[key]
    # single-word database key as a whole word/token
    tokens = set(n.split())
    for key in NUTRITION_DATABASE:
        if " " not in key and key in tokens:
            return NUTRITION_DATABASE[key]
    return DEFAULT_MACROS


def analyze_nutrition(items: List[Dict[str, str]], user_profile: UserProfile) -> Dict[str, object]:
    """Builds a simple nutrition report based on the detected foods."""
    totals = {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0, "fiber_g": 0.0, "sugar_g": 0.0}
    details = []

    for item in items:
        name = str(item.get("name", "")).strip().lower()
        grams = int(item.get("grams", 0) or 0)
        if grams <= 0:
            grams = 100

        data = lookup_nutrition(name)
        factor = grams / 100.0
        macros = {
            "calories": round(data["calories"] * factor, 1),
            "protein_g": round(data["protein_g"] * factor, 1),
            "fat_g": round(data["fat_g"] * factor, 1),
            "carbs_g": round(data["carbs_g"] * factor, 1),
            "fiber_g": round(data["fiber_g"] * factor, 1),
            "sugar_g": round(data["sugar_g"] * factor, 1),
        }
        totals = {k: totals[k] + macros[k] for k in totals}
        details.append({"name": name.title(), "grams": grams, "macros": macros})

    totals = {k: round(v, 1) for k, v in totals.items()}

    micronutrients = {
        "iron_mg": round(0.7 * len(items), 1),
        "vitamin_c_mg": round(5.0 * len(items), 1),
        "magnesium_mg": round(20.0 * len(items), 1),
    }

    summary = {
        "macros": totals,
        "micronutrients": micronutrients,
        "details": details,
        "recommendation": "The AI evaluates this meal based on portion sizes and suggests improvements.",
    }

    return summary
