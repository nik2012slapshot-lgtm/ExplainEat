"""Roboflow-Workflow-Anbindung: "Meal Ingredient Boxes".

Ruft den gehosteten Roboflow-Serverless-Workflow auf, der mit SAM3 mehrere
Lebensmittel pro Foto erkennt (Boxen + Klassen). Wird von ai_vision.py zuerst
versucht; ist kein API-Key gesetzt, wird das Modul still übersprungen und die
App fällt auf das lokale Modell zurück.

Geerdet an der echten Workflow-Definition (workflows_get) und einer echten
Beispielantwort (workflow_specs_run):

    Workflow-Output "predictions" =
        {
          "image": {"width": int, "height": int},
          "predictions": [
            {"x": float, "y": float,            # Box-MITTELPUNKT in Pixeln
             "width": float, "height": float,
             "confidence": float, "class": str, "class_id": int,
             "detection_id": str, "rle_mask": {...}}  # Maske: ignoriert
          ]
        }
    Workflow-Output "output_image" = base64-PNG (annotiert) — optional, groß.

API-Key:
    Aus Umgebungsvariable ROBOFLOW_API_KEY (siehe app.roboflow.com/settings/api).
    Niemals hartkodieren oder loggen.
"""

import base64
import io
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from PIL import Image

# --- Feste Workflow-Koordinaten (öffentliche Slugs, kein Geheimnis) ----------
API_URL = "https://serverless.roboflow.com"
WORKSPACE_NAME = "niks-workspace-uacfv"
WORKFLOW_ID = "meal-ingredient-boxes"
RUN_ENDPOINT = f"{API_URL}/{WORKSPACE_NAME}/workflows/{WORKFLOW_ID}"

API_KEY_ENV = "ROBOFLOW_API_KEY"

# Projektwurzel (eine Ebene über explain_eat/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv_once() -> None:
    """Lädt KEY=VALUE-Zeilen aus .env in os.environ (überschreibt nichts).

    Bewusst minimal und ohne Zusatzpaket; setzt nur Variablen, die noch nicht
    in der echten Umgebung stehen.
    """
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception as e:
        print(f"Hinweis: .env konnte nicht gelesen werden: {e}")


_load_dotenv_once()

# Erkennungen unter dieser Konfidenz werden verworfen. Höher = weniger
# Fehlerkennungen (Open-Vocabulary-SAM3 ist bei vielen Klassen rauschanfälliger).
CONF_THRESHOLD = 0.50

# Netzwerk-Verhalten
REQUEST_TIMEOUT = 30  # Sekunden
MAX_RETRIES = 3
BACKOFF_BASE = 1.5  # Sekunden: 1.5, 3.0, 6.0 ...


class RoboflowError(RuntimeError):
    """Basis für alle Roboflow-Integrationsfehler."""


class RoboflowConfigError(RoboflowError):
    """API-Key oder Konfiguration fehlt."""


class RoboflowRequestError(RoboflowError):
    """Aufruf des Workflows ist endgültig fehlgeschlagen."""


def _get_api_key() -> str:
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        raise RoboflowConfigError(
            f"Umgebungsvariable {API_KEY_ENV} ist nicht gesetzt. "
            "Key unter app.roboflow.com/settings/api holen und in .env eintragen."
        )
    return key


def _post_workflow(payload: dict) -> dict:
    """POST an den Workflow mit Timeout und Backoff-Retries. Gibt das rohe JSON.

    Loggt niemals den Body (kann base64-Bilder enthalten).
    """
    last_err: Optional[Exception] = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(RUN_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:  # Netzwerk/Timeout
            last_err = e
        else:
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError as e:
                    raise RoboflowRequestError("Antwort war kein gültiges JSON.") from e
            if resp.status_code in (401, 403):
                raise RoboflowConfigError(
                    f"Roboflow lehnte den API-Key ab (HTTP {resp.status_code})."
                )
            # 4xx außer Auth: erneuter Versuch zwecklos
            if 400 <= resp.status_code < 500 and resp.status_code not in (408, 429):
                raise RoboflowRequestError(
                    f"Workflow-Aufruf fehlgeschlagen (HTTP {resp.status_code})."
                )
            last_err = RoboflowRequestError(f"HTTP {resp.status_code}")

        if attempt < MAX_RETRIES:
            time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))

    raise RoboflowRequestError(
        f"Workflow nach {MAX_RETRIES} Versuchen nicht erreichbar."
    ) from last_err


def _first_output(raw: dict) -> dict:
    """Holt den ersten Output-Eintrag (ein Eintrag pro Eingabebild).

    Akzeptiert sowohl das REST-Format {"outputs": [ {...} ]} als auch eine
    direkt zurückgegebene Liste.
    """
    if isinstance(raw, dict) and "outputs" in raw:
        outputs = raw.get("outputs") or []
    elif isinstance(raw, list):
        outputs = raw
    else:
        outputs = [raw]
    if not outputs:
        raise RoboflowRequestError("Workflow lieferte keine Outputs.")
    first = outputs[0]
    if not isinstance(first, dict):
        raise RoboflowRequestError("Unerwartetes Output-Format.")
    return first


def _estimate_grams(area_ratio: float) -> int:
    """Grobe Mengenschätzung über den belegten Bildanteil (~20% Fläche ≈ 100 g)."""
    grams = int(round(area_ratio / 0.20 * 100))
    return max(20, min(grams, 500))


def _iter_prediction_blocks(output_entry: dict):
    """Liefert alle SAM3-Vorhersageblöcke eines Output-Eintrags.

    Der Workflow nutzt mehrere SAM3-Schritte (z. B. "predictions" und
    "predictions_2"), um das ~16-Klassen-Limit zu umgehen. Jeder zugehörige
    Output ist ein Dict mit einer "predictions"-Liste. Diese Funktion findet sie
    unabhängig von ihren Namen, sodass weitere SAM3-Schritte automatisch
    mitgezählt werden.
    """
    for value in output_entry.values():
        if isinstance(value, dict) and isinstance(value.get("predictions"), list):
            yield value


def parse_meal_predictions(output_entry: dict) -> List[Dict[str, object]]:
    """Wandelt einen Workflow-Output-Eintrag in App-Lebensmittel-Items um.

    Führt die Vorhersagen ALLER SAM3-Schritte zusammen. SAM3 liefert pro
    sichtbarem Stück eine eigene Erkennung (z. B. viele Brokkoli-Röschen);
    gleiche Zutaten werden zu EINEM Eintrag zusammengefasst: Gramm summiert,
    höchste Konfidenz übernommen, Anzahl der Einzelstücke in "count". Liest nur
    genutzte Felder; trägt rle_mask NICHT mit.
    """
    # Zusammenfassen pro Zutat (Reihenfolge des ersten Auftretens bewahren)
    aggregated: "Dict[str, Dict[str, float]]" = {}
    for block in _iter_prediction_blocks(output_entry):
        image_info = block.get("image") or {}
        img_w = float(image_info.get("width") or 0) or 1.0
        img_h = float(image_info.get("height") or 0) or 1.0
        img_area = img_w * img_h

        for det in block.get("predictions") or []:
            confidence = float(det.get("confidence", 0.0))
            if confidence < CONF_THRESHOLD:
                continue

            name = str(det.get("class", "unknown")).title()
            w = float(det.get("width", 0.0))
            h = float(det.get("height", 0.0))
            area_ratio = (w * h) / img_area if img_area else 0.0
            grams = _estimate_grams(area_ratio)

            if name in aggregated:
                agg = aggregated[name]
                agg["grams"] += grams
                agg["count"] += 1
                agg["confidence"] = max(agg["confidence"], confidence)
            else:
                aggregated[name] = {"grams": grams, "count": 1, "confidence": confidence}

    items: List[Dict[str, object]] = []
    for name, agg in aggregated.items():
        grams = int(agg["grams"])
        items.append({
            "name": name,
            "portion": f"~{grams} g",
            "grams": grams,
            "preparation": "detected",
            "confidence": round(agg["confidence"] * 100, 1),
            "count": int(agg["count"]),
        })

    items.sort(key=lambda d: d["confidence"], reverse=True)
    return items


def _save_annotated_image(output_entry: dict, save_path: Path) -> None:
    """Schreibt das base64-`output_image` auf die Festplatte (nie loggen)."""
    b64 = output_entry.get("output_image")
    if not isinstance(b64, str) or not b64:
        return
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(base64.b64decode(b64))
    except Exception as e:
        print(f"Hinweis: annotiertes Bild konnte nicht gespeichert werden: {e}")


class RoboflowMealDetector:
    """Client für den 'Meal Ingredient Boxes'-Workflow."""

    @staticmethod
    def is_configured() -> bool:
        return bool(os.environ.get(API_KEY_ENV, "").strip())

    def _run(self, image_value: dict, save_annotated_to: Optional[Path]) -> List[Dict[str, object]]:
        # use_cache=False: immer die aktuelle Workflow-Definition ausführen.
        # Roboflow cached die Workflow-Spec serverseitig; ohne dieses Flag würde
        # nach einer Workflow-Änderung minutenlang die alte Klassenliste laufen.
        payload = {
            "api_key": _get_api_key(),
            "inputs": {"image": image_value},
            "use_cache": False,
        }
        raw = _post_workflow(payload)
        entry = _first_output(raw)
        if save_annotated_to is not None:
            _save_annotated_image(entry, save_annotated_to)
        return parse_meal_predictions(entry)

    def detect_from_bytes(
        self, image_bytes: bytes, save_annotated_to: Optional[Path] = None
    ) -> List[Dict[str, object]]:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        return self._run({"type": "base64", "value": b64}, save_annotated_to)

    def detect_from_path(
        self, image_path: str, save_annotated_to: Optional[Path] = None
    ) -> List[Dict[str, object]]:
        # Neu kodieren über PIL -> robust gegen exotische Formate, immer JPEG.
        with Image.open(image_path) as img:
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG")
        return self.detect_from_bytes(buf.getvalue(), save_annotated_to)

    def detect_from_url(
        self, url: str, save_annotated_to: Optional[Path] = None
    ) -> List[Dict[str, object]]:
        if not url.lower().startswith("https://"):
            raise RoboflowRequestError("Nur https-URLs werden akzeptiert (http wird abgelehnt).")
        return self._run({"type": "url", "value": url}, save_annotated_to)


_detector: Optional[RoboflowMealDetector] = None


def get_meal_detector() -> Optional[RoboflowMealDetector]:
    """Singleton. Gibt None zurück, wenn kein ROBOFLOW_API_KEY gesetzt ist."""
    global _detector
    if not RoboflowMealDetector.is_configured():
        return None
    if _detector is None:
        _detector = RoboflowMealDetector()
    return _detector
