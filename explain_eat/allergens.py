"""Allergen-aware ingredient checking.

Goes beyond simple name matching: if a user is allergic to a category (e.g.
"nuts", "dairy"), ingredients that *contain* that allergen are caught even when
the word doesn't appear — e.g. pesto -> nuts, tzatziki -> dairy, mayonnaise ->
egg, bread/pasta -> gluten, shrimp -> shellfish, tofu -> soy.

Used by the recipe suggestions, the recipe generator and the shopping-list
warning so nothing unsafe is suggested.
"""

import re
from typing import Any, Dict, List, Set

# Allergen category -> whole-word keywords that indicate the allergen is present.
ALLERGEN_KEYWORDS: Dict[str, List[str]] = {
    "nuts": ["nut", "nuts", "peanut", "peanuts", "almond", "almonds", "cashew",
             "cashews", "walnut", "walnuts", "hazelnut", "hazelnuts", "pecan",
             "pecans", "pistachio", "pistachios", "pesto", "marzipan", "nutella"],
    "dairy": ["milk", "cheese", "yogurt", "yoghurt", "butter", "cream", "tzatziki",
              "mozzarella", "parmesan", "feta", "dairy", "cheddar"],
    "egg": ["egg", "eggs", "mayonnaise", "mayo", "aioli", "omelette", "omelet"],
    "gluten": ["gluten", "wheat", "bread", "breadcrumbs", "pasta", "noodle",
               "noodles", "couscous", "flour", "cracker", "crackers", "barley",
               "rye", "bulgur", "spaghetti"],
    "fish": ["fish", "salmon", "tuna", "cod", "mackerel", "sardine", "sardines",
             "anchovy", "anchovies", "trout"],
    "shellfish": ["shrimp", "shrimps", "prawn", "prawns", "crab", "lobster",
                  "shellfish", "scampi", "crayfish", "clam", "clams", "mussel",
                  "mussels", "oyster", "oysters", "squid", "calamari"],
    "soy": ["soy", "soya", "tofu", "edamame", "tempeh", "miso"],
    "sesame": ["sesame", "tahini"],
}

# What a user might type -> canonical category (English + German).
ALLERGY_SYNONYMS: Dict[str, str] = {
    "nut": "nuts", "nuts": "nuts", "tree nut": "nuts", "tree nuts": "nuts",
    "peanut": "nuts", "peanuts": "nuts", "nuss": "nuts", "nüsse": "nuts", "nuesse": "nuts",
    "milk": "dairy", "dairy": "dairy", "lactose": "dairy", "milch": "dairy", "laktose": "dairy",
    "egg": "egg", "eggs": "egg", "ei": "egg", "eier": "egg",
    "gluten": "gluten", "wheat": "gluten", "weizen": "gluten",
    "fish": "fish", "fisch": "fish",
    "shellfish": "shellfish", "seafood": "shellfish", "crustacean": "shellfish",
    "meeresfrüchte": "shellfish", "schalentiere": "shellfish", "krustentiere": "shellfish",
    "soy": "soy", "soya": "soy", "soja": "soy",
    "sesame": "sesame", "sesam": "sesame",
}

_word_cache: Dict[str, "re.Pattern"] = {}


def _matches_word(text: str, word: str) -> bool:
    pattern = _word_cache.get(word)
    if pattern is None:
        pattern = re.compile(r"\b" + re.escape(word) + r"\b")
        _word_cache[word] = pattern
    return bool(pattern.search(text))


def ingredient_allergen_categories(name: str) -> Set[str]:
    """Which allergen categories an ingredient belongs to."""
    n = name.lower()
    cats = set()
    for cat, keywords in ALLERGEN_KEYWORDS.items():
        if any(_matches_word(n, kw) for kw in keywords):
            cats.add(cat)
    return cats


def normalize_allergies(allergies) -> List[str]:
    if isinstance(allergies, str):
        allergies = allergies.split(",")
    return [str(a).strip().lower() for a in (allergies or []) if str(a).strip()]


def _user_terms_and_categories(allergies: List[str]):
    terms = normalize_allergies(allergies)
    cats: Set[str] = set()
    for a in terms:
        if a in ALLERGY_SYNONYMS:
            cats.add(ALLERGY_SYNONYMS[a])
        elif a in ALLERGEN_KEYWORDS:
            cats.add(a)
    return terms, cats


def ingredient_conflicts(name: str, allergies) -> bool:
    """True if an ingredient conflicts with the user's allergies."""
    terms, cats = _user_terms_and_categories(normalize_allergies(allergies))
    if not terms:
        return False
    n = name.lower()
    # 1) direct: the user named a specific food that appears as a whole word
    #    (whole-word so "egg" doesn't match "eggplant" / "veggie")
    if any(_matches_word(n, t) for t in terms):
        return True
    # 2) category: the user named an allergen class the ingredient belongs to
    if cats and (ingredient_allergen_categories(name) & cats):
        return True
    return False


def recipe_conflicts(recipe: Dict[str, Any], allergies) -> bool:
    """True if any ingredient of the recipe conflicts with the user's allergies."""
    terms = normalize_allergies(allergies)
    if not terms:
        return False
    for ing in recipe.get("ingredients", []):
        if ingredient_conflicts(str(ing.get("name", "")), terms):
            return True
    return False
