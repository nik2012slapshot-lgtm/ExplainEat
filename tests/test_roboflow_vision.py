"""Tests für die Roboflow-Workflow-Anbindung (Meal Ingredient Boxes).

Der Parser-Test nutzt eine ECHTE Beispielantwort des Workflows (erfasst über
die Roboflow-API) und braucht keinen API-Key. Der Live-Smoke-Test läuft nur,
wenn ROBOFLOW_API_KEY gesetzt ist, sonst wird er übersprungen.
"""

import os

import pytest

from explain_eat.roboflow_vision import (
    RoboflowMealDetector,
    parse_meal_predictions,
)

# Echte, gekürzte Workflow-Antwort (ein Output-Eintrag). Die rle_mask wurde
# absichtlich weggelassen — der Parser nutzt sie nicht.
REAL_OUTPUT_ENTRY = {
    "predictions": {
        "image": {"width": 1024, "height": 1536},
        "predictions": [
            {
                "width": 573,
                "height": 247,
                "x": 465.5,
                "y": 1006.5,
                "confidence": 0.92578125,
                "class_id": 0,
                "class": "salmon",
                "detection_id": "7e3b9dc7-896f-4514-8ade-c8e55ebb10bf",
                "parent_id": "image",
            },
            {
                "width": 300,
                "height": 280,
                "x": 200.0,
                "y": 400.0,
                "confidence": 0.77,
                "class_id": 1,
                "class": "broccoli",
                "detection_id": "abc",
            },
            {
                # zweites Brokkoli-Stück -> muss mit dem ersten zusammengefasst werden
                "width": 300,
                "height": 280,
                "x": 600.0,
                "y": 800.0,
                "confidence": 0.81,
                "class_id": 1,
                "class": "broccoli",
                "detection_id": "abc2",
            },
            {
                # unter dem Schwellenwert -> muss herausgefiltert werden
                "width": 50,
                "height": 50,
                "x": 10.0,
                "y": 10.0,
                "confidence": 0.10,
                "class_id": 6,
                "class": "lemon wedge",
                "detection_id": "low",
            },
        ],
    }
}

EXPECTED_ITEM_KEYS = {"name", "portion", "grams", "preparation", "confidence", "count"}


def test_parse_returns_expected_keys():
    items = parse_meal_predictions(REAL_OUTPUT_ENTRY)
    assert isinstance(items, list)
    assert items, "Es sollten Erkennungen über dem Schwellenwert übrig bleiben."
    for item in items:
        assert EXPECTED_ITEM_KEYS.issubset(item.keys())


def test_parse_filters_low_confidence():
    items = parse_meal_predictions(REAL_OUTPUT_ENTRY)
    names = {item["name"] for item in items}
    assert "Salmon" in names
    assert "Broccoli" in names
    assert "Lemon Wedge" not in names  # 0.10 < Schwellenwert


def test_parse_sorts_by_confidence_desc():
    items = parse_meal_predictions(REAL_OUTPUT_ENTRY)
    confidences = [item["confidence"] for item in items]
    assert confidences == sorted(confidences, reverse=True)
    assert items[0]["name"] == "Salmon"


def test_parse_aggregates_duplicates():
    items = parse_meal_predictions(REAL_OUTPUT_ENTRY)
    broccoli = [item for item in items if item["name"] == "Broccoli"]
    # zwei Brokkoli-Erkennungen -> genau EIN zusammengefasster Eintrag
    assert len(broccoli) == 1
    assert broccoli[0]["count"] == 2
    # höchste Konfidenz der beiden (0.81) wird übernommen
    assert broccoli[0]["confidence"] == 81.0


def test_portion_has_no_geschaetzt():
    items = parse_meal_predictions(REAL_OUTPUT_ENTRY)
    for item in items:
        assert "geschätzt" not in item["portion"]
        assert item["portion"].endswith(" g")


def test_parse_merges_multiple_sam3_blocks():
    """Der Workflow hat zwei SAM3-Schritte (predictions + predictions_2).
    Beide Blöcke müssen zusammengeführt werden."""
    two_step_entry = {
        "predictions": {
            "image": {"width": 1000, "height": 1000},
            "predictions": [
                {"x": 500, "y": 500, "width": 200, "height": 200,
                 "confidence": 0.9, "class": "salmon", "class_id": 3},
            ],
        },
        "predictions_2": {
            "image": {"width": 1000, "height": 1000},
            "predictions": [
                {"x": 300, "y": 300, "width": 150, "height": 150,
                 "confidence": 0.8, "class": "rice", "class_id": 0},
                {"x": 700, "y": 700, "width": 150, "height": 150,
                 "confidence": 0.7, "class": "rice", "class_id": 0},
            ],
        },
    }
    items = parse_meal_predictions(two_step_entry)
    names = {item["name"] for item in items}
    assert names == {"Salmon", "Rice"}
    rice = next(item for item in items if item["name"] == "Rice")
    assert rice["count"] == 2  # beide Reis-Erkennungen aus Block 2 zusammengefasst


def test_parse_handles_empty():
    assert parse_meal_predictions({}) == []
    assert parse_meal_predictions({"predictions": {"predictions": []}}) == []


def test_detector_not_configured_without_key(monkeypatch):
    monkeypatch.delenv("ROBOFLOW_API_KEY", raising=False)
    assert RoboflowMealDetector.is_configured() is False


@pytest.mark.skipif(
    not os.environ.get("ROBOFLOW_API_KEY"),
    reason="Live-Smoke-Test: ROBOFLOW_API_KEY nicht gesetzt.",
)
def test_live_smoke_detect_from_url():
    """Echter Aufruf gegen Roboflow — nur mit gesetztem Key."""
    detector = RoboflowMealDetector()
    items = detector.detect_from_url(
        "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=1024&q=80"
    )
    assert isinstance(items, list)
    for item in items:
        assert EXPECTED_ITEM_KEYS.issubset(item.keys())
