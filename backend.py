import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS

from explain_eat import ai_model
from explain_eat.ai_vision import load_food_labels
from explain_eat.auth import login_user, register_user
from explain_eat.explain import explain_meal, generate_shopping_recommendations
from explain_eat.nutrition import analyze_nutrition
from explain_eat.personalization import create_user_profile
from explain_eat.recipe_ai import generate_personalized_recipe, pick_inspiration, suggest_recipes
from explain_eat.recipes import build_shopping_list, get_recipe, load_recipes
from explain_eat.recognition import recognize_food

BASE_DIR = Path(__file__).resolve().parent
MEAL_STORE = BASE_DIR / "explain_eat" / "meals.json"
TRAINING_DIR = BASE_DIR / "explain_eat" / "training"
TRAINING_IMAGES = TRAINING_DIR / "images"
TRAINING_LABELS = TRAINING_DIR / "food_labels.txt"
MODELS_DIR = BASE_DIR / "explain_eat" / "models"
TRAINING_SCRIPT = BASE_DIR / "scripts" / "train_classifier.py"

app = Flask(__name__)
CORS(app)


def ensure_json(path: Path, default):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")


def load_json(path: Path, default):
    ensure_json(path, default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default


def save_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def build_profile(data: dict) -> dict:
    age = int(data.get("age", 30))
    weight = float(data.get("weight", 70.0))
    activity = data.get("activity", "moderate")
    goal = data.get("goal", "health")
    allergies = data.get("allergies", []) or []
    if isinstance(allergies, str):
        allergies = [item.strip() for item in allergies.split(",") if item.strip()]

    return {
        "age": age,
        "weight": weight,
        "activity_level": activity,
        "goal": goal,
        "allergies": allergies,
    }


def parse_date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.date().isoformat()
    except Exception:
        return value


def build_explanations(nutrition_report: dict, profile, profile_data: dict) -> tuple:
    """Returns (explanations, ai_powered). Uses ExplainEat's own trained model."""
    ai_tips = ai_model.generate_meal_explanation(nutrition_report, profile_data)
    if ai_tips:
        return ai_tips, ai_model.is_ready()
    return explain_meal(nutrition_report, profile), False


def start_training_process(epochs: int, batch_size: int, img_size: int, val_split: float, device: str) -> None:
    command = [
        sys.executable,
        str(TRAINING_SCRIPT),
        "--data", str(TRAINING_IMAGES),
        "--labels", str(TRAINING_LABELS),
        "--output", str(MODELS_DIR / "food_classifier.pth"),
        "--classes-output", str(MODELS_DIR / "food_classes.json"),
        "--metrics-output", str(MODELS_DIR / "metrics.json"),
        "--epochs", str(epochs),
        "--batch-size", str(batch_size),
        "--img-size", str(img_size),
        "--val-split", str(val_split),
        "--device", device,
    ]
    try:
        subprocess.Popen(command, cwd=str(BASE_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        raise RuntimeError(f"Training could not be started: {e}")


def load_meals() -> list[dict]:
    return load_json(MEAL_STORE, [])


def save_meals(meals: list[dict]) -> None:
    save_json(MEAL_STORE, meals)


def filter_meals(meals: list[dict], username: str | None = None, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
    results = meals
    if username:
        results = [m for m in results if str(m.get("username", "")).strip().lower() == username.strip().lower()]
    if date_from:
        results = [m for m in results if str(m.get("date", "")) >= date_from]
    if date_to:
        results = [m for m in results if str(m.get("date", "")) <= date_to]
    return results


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "ExplainEat backend is running."})


@app.route("/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    profile_data = build_profile(data)
    try:
        registered = register_user(username, password, profile_data)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid input."}), 400
    if registered:
        return jsonify({"success": True, "message": "Registration successful.", "profile": profile_data})
    return jsonify({"success": False, "message": "Username already taken."}), 409


@app.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    profile_data = login_user(username, password)
    if profile_data is not None:
        return jsonify({"success": True, "message": "Login successful.", "profile": profile_data})
    return jsonify({"success": False, "message": "Login failed."}), 401


@app.route("/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(force=True, silent=True) or {}
    profile_data = build_profile(data)
    profile = create_user_profile(**profile_data)
    manual_items = data.get("food_items") or []
    if isinstance(manual_items, str):
        manual_items = [item.strip() for item in manual_items.split("\n") if item.strip()]
    detected_items = recognize_food(None, manual_items=manual_items)
    nutrition_report = analyze_nutrition(detected_items, profile)
    explanations, ai_powered = build_explanations(nutrition_report, profile, profile_data)
    shopping_recommendations = generate_shopping_recommendations(
        nutrition_report, detected_items, profile
    )
    return jsonify({
        "success": True,
        "profile": profile_data,
        "detected_items": detected_items,
        "nutrition_report": nutrition_report,
        "explanations": explanations,
        "ai_powered": ai_powered,
        "shopping_recommendations": shopping_recommendations,
    })


@app.route("/analyze_image", methods=["POST"])
def api_analyze_image():
    profile_data = build_profile(request.form.to_dict())
    profile = create_user_profile(**profile_data)
    image_file = request.files.get("image")
    if image_file is None:
        return jsonify({"success": False, "message": "No image uploaded."}), 400
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        image_file.save(temp_file.name)
        temp_path = temp_file.name
    try:
        detected_items = recognize_food(temp_path)
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass
    nutrition_report = analyze_nutrition(detected_items, profile)
    explanations, ai_powered = build_explanations(nutrition_report, profile, profile_data)
    shopping_recommendations = generate_shopping_recommendations(
        nutrition_report, detected_items, profile
    )
    return jsonify({
        "success": True,
        "profile": profile_data,
        "detected_items": detected_items,
        "nutrition_report": nutrition_report,
        "explanations": explanations,
        "ai_powered": ai_powered,
        "shopping_recommendations": shopping_recommendations,
    })


@app.route("/recipes", methods=["GET"])
def api_recipes():
    return jsonify({"success": True, "recipes": load_recipes(), "ai_enabled": ai_model.is_ready()})


@app.route("/recipes/suggest", methods=["POST"])
def api_recipes_suggest():
    data = request.get_json(force=True, silent=True) or {}
    profile_data = build_profile(data)
    try:
        limit = int(data.get("limit", 12))
    except (TypeError, ValueError):
        limit = 12
    suggestions = suggest_recipes(profile_data, limit)
    return jsonify({
        "success": True,
        "profile": profile_data,
        "suggestions": suggestions,
        "ai_powered": ai_model.is_ready(),
    })


@app.route("/recipes/shopping", methods=["POST"])
def api_recipe_shopping():
    data = request.get_json(force=True, silent=True) or {}
    recipe_id = str(data.get("recipe_id", "")).strip()
    recipe = get_recipe(recipe_id)
    if recipe is None:
        return jsonify({"success": False, "message": "Recipe not found."}), 404

    profile_data = build_profile(data)
    shopping_list = build_shopping_list(recipe, profile_data)
    advice = ai_model.generate_shopping_advice(shopping_list, profile_data)
    return jsonify({
        "success": True,
        "profile": profile_data,
        "shopping_list": shopping_list,
        "advice": advice,
        "ai_powered": ai_model.is_ready(),
    })


@app.route("/recipes/generate", methods=["POST"])
def api_recipe_generate():
    data = request.get_json(force=True, silent=True) or {}
    profile_data = build_profile(data)

    base_id = str(data.get("base_recipe_id", "")).strip()
    base = get_recipe(base_id) if base_id else None
    if base is None:
        base = pick_inspiration()

    recipe = generate_personalized_recipe(profile_data, base)
    # The generated recipe is already personalized — present its ingredients
    # directly as the shopping list (no further scaling).
    shopping_list = {
        "recipe_id": recipe["id"],
        "recipe_name": recipe["name"],
        "description": recipe["description"],
        "steps": recipe.get("steps", []),
        "scale_factor": 1.0,
        "items": [
            {"name": i["name"], "grams": i["grams"], "base_grams": i["grams"],
             "allergy_warning": False}
            for i in recipe["ingredients"]
        ],
    }
    advice = ai_model.generate_shopping_advice(shopping_list, profile_data)
    return jsonify({
        "success": True,
        "profile": profile_data,
        "recipe": recipe,
        "shopping_list": shopping_list,
        "advice": advice,
        "ai_powered": ai_model.is_ready(),
    })


@app.route("/training/status", methods=["GET"])
def training_status():
    labels = load_food_labels()
    image_counts = {}
    if TRAINING_IMAGES.exists():
        for label_dir in sorted(TRAINING_IMAGES.iterdir()):
            if label_dir.is_dir():
                image_counts[label_dir.name] = len([*label_dir.glob("*.jpg"), *label_dir.glob("*.png")])
    model_file = MODELS_DIR / "food_classifier.pth"
    metrics_file = MODELS_DIR / "metrics.json"
    metrics = load_json(metrics_file, {}) if metrics_file.exists() else {}
    return jsonify({
        "success": True,
        "labels": labels,
        "image_counts": image_counts,
        "model_available": model_file.exists(),
        "metrics": metrics,
    })


@app.route("/training/retrain", methods=["POST"])
def training_retrain():
    data = request.get_json(force=True, silent=True) or {}
    if not TRAINING_IMAGES.exists() or not any(TRAINING_IMAGES.iterdir()):
        return jsonify({"success": False, "message": "No training images found. Place images in explain_eat/training/images/<label>/."}), 400

    epochs = int(data.get("epochs", 8))
    batch_size = int(data.get("batch_size", 24))
    img_size = int(data.get("img_size", 224))
    val_split = float(data.get("val_split", 0.15))
    device = data.get("device", "cpu")

    try:
        start_training_process(epochs, batch_size, img_size, val_split, device)
        return jsonify({"success": True, "message": "Retraining started. The model is being trained in the background."})
    except RuntimeError as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/meals", methods=["GET", "POST"])
def meals():
    if request.method == "GET":
        username = request.args.get("username")
        date_from = request.args.get("from")
        date_to = request.args.get("to")
        meals_data = load_meals()
        filtered = filter_meals(meals_data, username=username, date_from=date_from, date_to=date_to)
        return jsonify({"success": True, "meals": filtered})

    body = request.get_json(force=True, silent=True) or {}
    username = body.get("username", "guest").strip()
    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400

    meal_date = parse_date(body.get("date", datetime.now().date().isoformat()))
    meal_time = body.get("time", "12:00").strip()
    items = body.get("items", [])
    if isinstance(items, str):
        items = [line.strip() for line in items.split("\n") if line.strip()]
    notes = body.get("notes", "").strip()

    meals_data = load_meals()
    meal_id = str(len(meals_data) + 1)
    meal_entry = {
        "id": meal_id,
        "username": username,
        "date": meal_date,
        "time": meal_time,
        "items": items,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }
    meals_data.append(meal_entry)
    save_meals(meals_data)
    return jsonify({"success": True, "meal": meal_entry})


@app.route("/meals/<meal_id>", methods=["DELETE"])
def delete_meal(meal_id: str):
    meals_data = load_meals()
    remaining = [meal for meal in meals_data if meal.get("id") != meal_id]
    if len(remaining) == len(meals_data):
        return jsonify({"success": False, "message": "Meal not found."}), 404
    save_meals(remaining)
    return jsonify({"success": True, "message": "Meal deleted."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
