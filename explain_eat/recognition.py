from typing import Any, Dict, List, Optional, Union
from .ai_vision import get_food_ai


def _parse_grams(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    digits = ''.join(ch for ch in text if ch.isdigit())
    if digits:
        try:
            return int(digits)
        except ValueError:
            pass
    return None


def recognize_food(
    image_path: Optional[str] = None,
    manual_items: Optional[List[Union[str, Dict[str, Any]]]] = None,
    image_bytes: Optional[bytes] = None,
) -> List[Dict[str, str]]:
    """Food recognition: uses the AI model or manual input."""

    # If manual items are present, use them
    if manual_items:
        items = []
        for raw_item in manual_items:
            if raw_item is None:
                continue

            grams = None
            if isinstance(raw_item, dict):
                name = str(raw_item.get("name", "")).strip()
                grams = _parse_grams(raw_item.get("grams") or raw_item.get("amount") or raw_item.get("portion"))
            else:
                line = str(raw_item).strip()
                if not line:
                    continue

                if "," in line:
                    name, portion = [part.strip() for part in line.split(",", 1)]
                elif "-" in line:
                    name, portion = [part.strip() for part in line.split("-", 1)]
                else:
                    name, portion = line, "1 Portion"
                grams = _parse_grams(portion)
                name = name

            if not name:
                continue

            portion_text = f"{grams} g" if grams else "1 Portion"
            items.append({
                "name": name.title(),
                "portion": portion_text,
                "grams": grams if grams is not None else 0,
                "preparation": "manual",
            })
        return items
    
    # If an image path is present, use the AI model
    if image_path:
        try:
            ai = get_food_ai()
            if ai is None or not hasattr(ai, "recognize_from_image"):
                print("AI model not available — using fallback.")
                return [{"name": "Model not available", "portion": "1 portion", "preparation": "fallback", "confidence": 0}]
            return ai.recognize_from_image(image_path)
        except Exception as e:
            print(f"AI model error: {e}")
            return [{"name": "Image processing error", "portion": "1 portion", "preparation": "error", "confidence": 0}]

    # If image data was passed as bytes (e.g. web upload), use the AI from bytes
    if image_bytes is not None:
        try:
            ai = get_food_ai()
            if ai is None or not hasattr(ai, "recognize_from_bytes"):
                print("AI model not available — using fallback for bytes.")
                return [{"name": "Model not available", "portion": "1 portion", "preparation": "fallback", "confidence": 0}]
            return ai.recognize_from_bytes(image_bytes)
        except Exception as e:
            print(f"AI model error while processing bytes: {e}")
            return [{"name": "Image processing error", "portion": "1 portion", "preparation": "error", "confidence": 0}]

    # Fallback: dummy examples
    return [
        {"name": "Whole-grain bread", "portion": "2 slices", "preparation": "toasted"},
        {"name": "Avocado", "portion": "1/2 fruit", "preparation": "raw"},
    ]
