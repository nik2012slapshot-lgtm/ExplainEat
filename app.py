import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
import anthropic

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "explaineat-secret-2026")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Du bist ExplainEat, ein freundlicher KI-Ernährungscoach.

Deine Aufgabe:
- Analysiere Mahlzeiten und erkläre sie verständlich (KEIN Fachjargon)
- Erkläre WARUM etwas gut oder weniger gut ist
- Schätze Nährwerte (Kalorien, Protein, Kohlenhydrate, Fett, Ballaststoffe)
- Erkenne Defizite und gib konkrete Verbesserungsvorschläge
- Bleibe motivierend, nicht belehrend

Antworte immer auf Deutsch in folgendem JSON-Format:
{
  "erklaerung": "Verständliche Erklärung der Mahlzeit (2-3 Sätze)",
  "naehrwerte": {
    "kalorien": 0,
    "protein_g": 0,
    "kohlenhydrate_g": 0,
    "fett_g": 0,
    "ballaststoffe_g": 0
  },
  "positives": ["Punkt 1", "Punkt 2"],
  "verbesserungen": ["Tipp 1", "Tipp 2"],
  "fehlendes": "Was heute noch fehlt und warum"
}

Wichtig: Stelle KEINE medizinischen Diagnosen. Bei Hinweisen auf Essstörungen oder extreme Diäten weise sanft auf professionelle Hilfe hin."""


def analyze_meal(meal_text: str, daily_log: list, user_profile: dict) -> dict:
    profile_info = f"""
Nutzerprofil: Alter {user_profile.get('age', '?')},
Gewicht {user_profile.get('weight', '?')} kg,
Ziel: {user_profile.get('goal', 'gesunde Ernährung')}
"""
    log_info = ""
    if daily_log:
        log_info = f"\nBisher heute gegessen: {', '.join(daily_log)}"

    user_message = f"{profile_info}{log_info}\n\nAktuelle Mahlzeit: {meal_text}"

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = message.content[0].text
    # Extrahiere JSON aus der Antwort
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    if start != -1 and end > start:
        return json.loads(response_text[start:end])
    return {"erklaerung": response_text, "naehrwerte": {}, "positives": [], "verbesserungen": [], "fehlendes": ""}


def generate_shopping_list(goal: str, deficits: list) -> str:
    prompt = f"""Erstelle eine kurze, praktische Einkaufsliste für jemanden mit dem Ziel: "{goal}".
Erkannte Defizite: {', '.join(deficits) if deficits else 'keine spezifischen'}.
Antworte mit 8-10 konkreten Lebensmitteln, je mit einem kurzen Grund (1 Satz). Auf Deutsch."""

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def generate_recipe(ingredients: str, goal: str, time_minutes: int) -> str:
    prompt = f"""Erstelle ein einfaches Rezept.
Verfügbare Zutaten: {ingredients}
Ziel: {goal}
Maximale Zeit: {time_minutes} Minuten
Antworte mit: Rezeptname, Zutaten-Liste, kurze Schritt-für-Schritt-Anleitung. Auf Deutsch."""

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


@app.route("/")
def index():
    if "daily_log" not in session:
        session["daily_log"] = []
    if "user_profile" not in session:
        session["user_profile"] = {"age": 25, "weight": 70, "goal": "gesunde Ernährung"}
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    meal = data.get("meal", "").strip()
    if not meal:
        return jsonify({"error": "Bitte gib eine Mahlzeit ein."}), 400

    if "daily_log" not in session:
        session["daily_log"] = []

    result = analyze_meal(meal, session["daily_log"], session.get("user_profile", {}))

    session["daily_log"] = session["daily_log"] + [meal]
    session.modified = True

    return jsonify({"result": result, "meal": meal})


@app.route("/shopping-list", methods=["POST"])
def shopping_list():
    data = request.get_json()
    goal = data.get("goal", "gesunde Ernährung")
    deficits = data.get("deficits", [])
    result = generate_shopping_list(goal, deficits)
    return jsonify({"list": result})


@app.route("/recipe", methods=["POST"])
def recipe():
    data = request.get_json()
    ingredients = data.get("ingredients", "")
    goal = data.get("goal", "gesunde Ernährung")
    time_minutes = data.get("time", 20)
    result = generate_recipe(ingredients, goal, time_minutes)
    return jsonify({"recipe": result})


@app.route("/profile", methods=["POST"])
def update_profile():
    data = request.get_json()
    session["user_profile"] = {
        "age": data.get("age", 25),
        "weight": data.get("weight", 70),
        "goal": data.get("goal", "gesunde Ernährung"),
    }
    session.modified = True
    return jsonify({"status": "ok"})


@app.route("/reset-day", methods=["POST"])
def reset_day():
    session["daily_log"] = []
    session.modified = True
    return jsonify({"status": "Neuer Tag gestartet"})


@app.route("/daily-summary", methods=["GET"])
def daily_summary():
    log = session.get("daily_log", [])
    if not log:
        return jsonify({"summary": "Noch keine Mahlzeiten heute eingetragen."})

    prompt = f"""Erstelle eine kurze Tages-Zusammenfassung für folgende Mahlzeiten: {', '.join(log)}.
Gib: Gesamteindruck, was gut war, was morgen besser sein könnte. Max. 3 Sätze. Auf Deutsch."""

    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return jsonify({"summary": message.content[0].text, "meals": log})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
