"""Recipe store and body-weight-aware shopping-list scaling.

Recipes are loaded from recipes.json. Each recipe lists ingredients in grams for
a reference person (about 70 kg, moderate activity, "health" goal). The shopping
list for a specific user is scaled from that baseline using their body weight,
activity level and goal, so a heavier person training for muscle gets larger
portions than a lighter person aiming to lose weight.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

RECIPES_PATH = Path(__file__).parent / "recipes.json"

# Optional external recipe source. Set RECIPE_API_URL in .env to a URL that
# returns recipes (either a JSON list, or {"recipes": [...]}) in the same schema
# as recipes.json. Remote recipes are merged with the local ones.
RECIPE_API_URL_ENV = "RECIPE_API_URL"
_REMOTE_TTL_SECONDS = 300
_remote_cache: Dict[str, Any] = {"ts": 0.0, "data": []}
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _ensure_env() -> None:
    """Loads .env so RECIPE_API_URL is available even if recipes is imported first."""
    if os.environ.get(RECIPE_API_URL_ENV):
        return
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass


def _is_valid_recipe(r: Any) -> bool:
    return isinstance(r, dict) and "id" in r and isinstance(r.get("ingredients"), list)


def load_remote_recipes() -> List[Dict[str, Any]]:
    """Fetches recipes from RECIPE_API_URL (cached). Returns [] if unset or on error."""
    _ensure_env()
    url = os.environ.get(RECIPE_API_URL_ENV, "").strip()
    if not url:
        return []
    now = time.time()
    if _remote_cache["data"] and now - _remote_cache["ts"] < _REMOTE_TTL_SECONDS:
        return _remote_cache["data"]
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            print(f"Recipe API returned HTTP {resp.status_code}; using cached/local.")
            return _remote_cache["data"]
        payload = resp.json()
        items = payload.get("recipes") if isinstance(payload, dict) else payload
        recipes = []
        for r in (items or []):
            if _is_valid_recipe(r):
                r = dict(r)
                r["source"] = "api"
                recipes.append(r)
        _remote_cache["data"] = recipes
        _remote_cache["ts"] = now
        print(f"Loaded {len(recipes)} recipes from RECIPE_API_URL.")
        return recipes
    except Exception as e:
        print(f"Recipe API fetch failed ({e}); using cached/local.")
        return _remote_cache["data"]

# Reference person the base recipe amounts are written for.
REFERENCE_WEIGHT_KG = 70.0

GOAL_FACTORS = {"muscle": 1.15, "weight_loss": 0.85, "health": 1.0}
ACTIVITY_FACTORS = {"low": 0.9, "moderate": 1.0, "high": 1.15}

# Bounds so scaling never produces absurd amounts.
MIN_SCALE = 0.5
MAX_SCALE = 2.0


def load_recipes() -> List[Dict[str, Any]]:
    if not RECIPES_PATH.exists():
        return []
    try:
        data = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error loading recipes.json: {e}")
        return []
    if not isinstance(data, list):
        return []

    # Be forgiving if recipes were accidentally grouped in nested [ ] arrays:
    # flatten one level and keep only valid recipe objects.
    recipes: List[Dict[str, Any]] = []
    for entry in data:
        candidates = entry if isinstance(entry, list) else [entry]
        for r in candidates:
            if _is_valid_recipe(r):
                recipes.append(r)

    # Merge in recipes from the optional external API (deduped by id).
    seen = {str(r.get("id")) for r in recipes}
    for r in load_remote_recipes():
        if str(r.get("id")) not in seen:
            recipes.append(r)
            seen.add(str(r.get("id")))
    return recipes


def get_recipe(recipe_id: str) -> Dict[str, Any] | None:
    for recipe in load_recipes():
        if str(recipe.get("id")) == str(recipe_id):
            return recipe
    return None


def compute_scale_factor(profile: Dict[str, Any]) -> float:
    """Derives a portion scale factor from the user's profile."""
    try:
        weight = float(profile.get("weight", REFERENCE_WEIGHT_KG))
    except (TypeError, ValueError):
        weight = REFERENCE_WEIGHT_KG

    weight_factor = weight / REFERENCE_WEIGHT_KG
    goal_factor = GOAL_FACTORS.get(str(profile.get("goal", "health")).lower(), 1.0)
    activity_factor = ACTIVITY_FACTORS.get(
        str(profile.get("activity_level", profile.get("activity", "moderate"))).lower(), 1.0
    )

    scale = weight_factor * goal_factor * activity_factor
    return round(max(MIN_SCALE, min(scale, MAX_SCALE)), 2)


def _matches_allergy(name: str, allergies: List[str]) -> bool:
    from .allergens import ingredient_conflicts
    return ingredient_conflicts(name, allergies)


def build_shopping_list(recipe: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Scales a recipe's ingredients to the user's profile and flags allergies."""
    scale = compute_scale_factor(profile)
    allergies = profile.get("allergies") or []
    if isinstance(allergies, str):
        allergies = [a.strip() for a in allergies.split(",") if a.strip()]

    items: List[Dict[str, Any]] = []
    for ing in recipe.get("ingredients", []):
        name = str(ing.get("name", "")).strip()
        if not name:
            continue
        try:
            base_grams = float(ing.get("grams", 0))
        except (TypeError, ValueError):
            base_grams = 0.0
        grams = int(round(base_grams * scale))
        items.append({
            "name": name,
            "grams": grams,
            "base_grams": int(base_grams),
            "allergy_warning": _matches_allergy(name, allergies),
        })

    return {
        "recipe_id": recipe.get("id"),
        "recipe_name": recipe.get("name"),
        "description": recipe.get("description", ""),
        "steps": recipe.get("steps", []),
        "scale_factor": scale,
        "items": items,
    }
