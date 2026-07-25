"""YOLO-basierte Lebensmittel-Objekterkennung (mehrere Items pro Foto).

Lädt das trainierte Modell explain_eat/models/food_detector.pt und gibt für ein
Bild eine Liste erkannter Lebensmittel mit Konfidenz und Bounding-Box zurück.

Wird automatisch von ai_vision.py benutzt, sobald food_detector.pt existiert und
ultralytics installiert ist. Fehlt eines davon, gibt get_food_detector() None
zurück und ai_vision.py fällt auf den alten Classifier/Zero-Shot zurück.
"""

import io
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except Exception:  # pragma: no cover
    YOLO = None
    HAS_YOLO = False

MODEL_DIR = Path(__file__).parent / "models"
DETECTOR_PATH = MODEL_DIR / "food_detector.pt"

# Mindest-Konfidenz, ab der eine Erkennung übernommen wird.
CONF_THRESHOLD = 0.25


class FoodDetectorYOLO:
    def __init__(self, model_path: Path = DETECTOR_PATH):
        self.model = YOLO(str(model_path))
        self.names = self.model.names  # {0: 'beef', 1: 'chicken', ...}
        print(f"YOLO-Detektor geladen mit {len(self.names)} Klassen: "
              f"{list(self.names.values())}")

    def _estimate_grams(self, box_area_ratio: float) -> int:
        """Grobe Mengenschätzung anhand des belegten Bildanteils.

        Reine Heuristik: ein Item, das ~20% des Bildes füllt, wird auf ~100 g
        geschätzt. Für echte Mengen bräuchte man eine Referenz (Teller/Münze).
        """
        grams = int(round(box_area_ratio / 0.20 * 100))
        return max(20, min(grams, 500))

    def detect(self, img: Image.Image) -> List[Dict[str, object]]:
        results = self.model.predict(img, conf=CONF_THRESHOLD, verbose=False)
        if not results:
            return []

        res = results[0]
        img_area = float(res.orig_shape[0] * res.orig_shape[1]) or 1.0

        detections: List[Dict[str, object]] = []
        for box in res.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            box_area = max(0.0, (x2 - x1) * (y2 - y1))
            area_ratio = box_area / img_area
            label = self.names.get(cls_id, "unknown")
            grams = self._estimate_grams(area_ratio)

            detections.append({
                "name": str(label).title(),
                "portion": f"~{grams} g",
                "grams": grams,
                "preparation": "detected",
                "confidence": round(conf * 100, 1),
                "bbox": [round(x1), round(y1), round(x2), round(y2)],
            })

        # stärkste Erkennungen zuerst
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections

    def detect_from_bytes(self, image_bytes: bytes) -> List[Dict[str, object]]:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self.detect(img)

    def detect_from_path(self, image_path: str) -> List[Dict[str, object]]:
        img = Image.open(image_path).convert("RGB")
        return self.detect(img)


_detector: Optional[FoodDetectorYOLO] = None
_tried_load = False


def get_food_detector() -> Optional[FoodDetectorYOLO]:
    """Singleton. Gibt None zurück, wenn ultralytics oder Modell fehlen."""
    global _detector, _tried_load
    if _tried_load:
        return _detector
    _tried_load = True

    if not HAS_YOLO:
        print("Hinweis: ultralytics nicht installiert — YOLO-Detektor inaktiv.")
        return None
    if not DETECTOR_PATH.exists():
        print(f"Hinweis: kein YOLO-Modell unter {DETECTOR_PATH} — "
              "zuerst scripts/train_yolo.py ausführen.")
        return None
    try:
        _detector = FoodDetectorYOLO()
    except Exception as e:
        print(f"Fehler beim Laden des YOLO-Detektors: {e}")
        _detector = None
    return _detector
