# ExplainEat

ExplainEat ist eine Ernährungs-App mit einer **eigenen, lokal trainierten KI**
(neuronales Netz). Sie erkennt Lebensmittel auf Fotos, bewertet Mahlzeiten
personalisiert (Gewicht, Ziel, Aktivität, Allergien), **schlägt passende Rezepte
vor** und **generiert eigene Rezepte** – alles auf den Nutzer zugeschnitten.

*Eingereicht von Nik – KI Challenge 2026*

---

## Wettbewerbs-Abgabe

| | Datei |
|---|---|
| **Video-Pitch** (2 Min) | [`ExplainEat_Pitch_v4.mp4`](ExplainEat_Pitch_v4.mp4) |
| **Screen Recording der App** | [`ExplainEat_App_Demo.mp4`](ExplainEat_App_Demo.mp4) |
| **Kritische Reflexion** | [`kritische_reflexion.md`](kritische_reflexion.md) |
| **Code** | dieses Repository (siehe Schnellstart unten) |

---

## Schnellstart (Web-App)

Zwei Prozesse: das **Backend** (API, Port 5000) und die **App** (Port 8080).

```powershell
# 1) Abhängigkeiten (einmalig)
python -m pip install -r requirements.txt

# 2) Backend starten
python backend.py

# 3) In einem zweiten Fenster: die gebaute Web-App ausliefern
python -m http.server 8080 --directory flutter_app/build/web
```

Dann im Browser **http://localhost:8080** öffnen.

> Nach Änderungen an der Flutter-UI einmal neu bauen:
> `cd flutter_app && flutter build web --release`

Alternativ für Entwicklung direkt: `cd flutter_app && flutter run`.

---

## Die App (3 Tabs)

- **Analyze** – Foto hochladen oder Lebensmittel manuell eingeben → Erkennung,
  Nährwerte und KI-Bewertung/Tipps.
- **Shopping** – KI-**Empfehlungen** („Recommended for you"), 1000 Rezepte
  (allergiegefiltert) und **„Generate a recipe for me"** (KI baut ein Rezept).
  Klick auf ein Rezept → Einkaufsliste (auf dich skaliert) + KI-Tipp als Overlay.
- **Recommendations** – Nährwert-Zusammenfassung und KI-Erklärungen zur letzten
  Analyse.

---

## Eigene KI (lokal trainiertes neuronales Netz)

Kern der App ist ein **selbst trainiertes PyTorch-Netz** (`NutritionNet`) – kein
externes/vorgefertigtes Modell. Es bekommt Profil + Mahlzeit-Makros und liefert:

- einen **Mahlzeit-Score** (0–100) passend zum Ziel,
- Flags (Protein niedrig, Ballaststoffe niedrig, Zucker hoch, Kalorien unpassend),
- eine **Empfehlungsklasse** (mehr Protein / Gemüse / komplexe Kohlenhydrate / ausgewogen).

Daraus werden Texte formuliert – die **Entscheidung** trifft das Netz.

| Was | Datei |
|-----|-------|
| Netz + Inferenz (`NutritionNet`, `predict`) | `explain_eat/ai_model.py` |
| Training | `scripts/train_ai_model.py` → `explain_eat/models/nutrition_ai.pt` |
| KI-Rezept-Empfehlung & -Generierung | `explain_eat/recipe_ai.py` |

**Modell trainieren** (einmalig; wird beim nächsten Backend-Start automatisch geladen):

```powershell
python scripts/train_ai_model.py --samples 30000 --epochs 40
```

Ohne trainiertes Modell nutzt die App eine transparente Heuristik als Fallback
(dann ohne „AI powered"-Badge).

**KI-Endpunkte:** `POST /analyze`, `POST /analyze_image` (Bewertung/Erklärung),
`POST /recipes/suggest` (Empfehlungen), `POST /recipes/generate` (neues Rezept),
`POST /recipes/shopping` (skalierte Einkaufsliste + Tipp).

---

## Rezepte

- **Lokal:** `explain_eat/recipes.json` (aktuell 1000 Rezepte). Schema pro Rezept:
  `id`, `name`, `description`, `ingredients` (Name + Gramm für eine ~70-kg-Referenz),
  optionale `steps`, `tags`.
- **Neu generieren:** `python scripts/generate_recipes.py --target 1000`
  (behält deine echten Rezepte, füllt auf, Backup als `recipes.backup*.json`).
- **Aus einer API laden:** `RECIPE_API_URL` in der `.env` setzen (JSON-Liste oder
  `{"recipes": [...]}` im gleichen Schema) – wird mit den lokalen gemischt.
- **Allergien:** Rezepte mit unverträglichen Zutaten werden **nicht** vorgeschlagen;
  der Generator meidet sie ebenfalls.

---

## Bilderkennung mehrerer Zutaten (Roboflow)

Foto-Uploads werden über den gehosteten Roboflow-Workflow **„Meal Ingredient
Boxes"** (SAM3) analysiert, der mehrere Lebensmittel pro Foto erkennt. Anbindung:
`explain_eat/roboflow_vision.py`. Ohne API-Key fällt die App still auf ein lokales
Modell zurück.

**Einrichtung:**

```powershell
Copy-Item .env.example .env   # dann .env öffnen und Keys setzen
```

`.env` (in `.gitignore`, nicht committen):

```
ROBOFLOW_API_KEY=...   # Foto-Erkennung; Key: https://app.roboflow.com/settings/api
RECIPE_API_URL=        # optional: externe Rezept-API
```

> Der Workflow nutzt zwei SAM3-Schritte (max. ~16 Klassen je Schritt); die App
> führt beide Ergebnisse zusammen (`_iter_prediction_blocks`) und setzt
> `use_cache=False`, damit Workflow-Änderungen sofort greifen.

Test: `python -m pytest tests/test_roboflow_vision.py -v`

---

## Skripte

Alle liegen im Ordner **`scripts/`**:

| Skript | Zweck |
|--------|-------|
| `train_ai_model.py` | Trainiert die **eigene KI** (Ernährungs-Netz) → `models/nutrition_ai.pt` |
| `generate_recipes.py` | Erzeugt viele gültige Rezepte in `recipes.json` |
| `train_yolo.py` | Optional: lokales YOLO-Objekterkennungsmodell (Foto) trainieren |
| `train_classifier.py` | Optional: lokales Single-Label-Bildmodell (Fallback) trainieren |
| `check_cameras.py` | Listet verfügbare Kameras (Diagnose) |

---

## Projektstruktur

- `backend.py` – Flask-API (Endpunkte für Analyse, Rezepte, KI)
- `app.py` – CLI/Tkinter-GUI (Alternative zum Web-Frontend)
- `explain_eat/` – Kernpaket
  - `ai_model.py` – **eigene KI** (neuronales Netz + Inferenz)
  - `recipe_ai.py` – KI-Rezept-Empfehlung & -Generierung
  - `recipes.py` – Rezept-Laden (lokal + API) und Skalierung
  - `nutrition.py` – Nährwert-Datenbank + intelligente Zutaten-Zuordnung
  - `roboflow_vision.py` – Foto-Erkennung (Roboflow-Workflow)
  - `recognition.py`, `explain.py`, `personalization.py`, `auth.py`
  - `recipes.json`, `models/` (trainierte Modelle)
- `flutter_app/` – Flutter-Frontend (Web-App)
- `scripts/` – Trainings-/Hilfsskripte (siehe oben)
- `tests/` – Unit-Tests
