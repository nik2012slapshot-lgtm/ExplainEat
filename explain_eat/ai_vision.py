import io
import json
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from .yolo_vision import get_food_detector
from .roboflow_vision import get_meal_detector

# Optional imports for model training and inference
try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
except Exception as _e:
    torch = None
    nn = None
    models = None
    transforms = None

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except Exception as _e:
    pipeline = None
    HAS_TRANSFORMERS = False
    print(f"Warning: transformers/pipeline not available: {_e}")

TRAINING_DIR = Path(__file__).parent.parent / "training"
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "food_classifier.pth"
CLASS_MAP_PATH = MODEL_DIR / "food_classes.json"
LABELS_FILE = TRAINING_DIR / "food_labels.txt"


def load_food_labels() -> List[str]:
    if LABELS_FILE.exists():
        try:
            labels = [line.strip() for line in LABELS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
            if labels:
                print(f"Loaded {len(labels)} custom food labels from {LABELS_FILE}")
                return labels
        except Exception as e:
            print(f"Error loading food_labels.txt: {e}")

    return [
        "bread", "vegetable", "fruit", "meat", "fish", "dairy",
        "pasta", "rice", "egg", "legume", "soup", "dessert",
        "beverage", "sandwich", "salad", "pizza", "burger", "chicken",
        "beef", "pork", "apple", "banana", "orange", "broccoli",
        "carrot", "spinach", "tomato", "cheese", "milk", "yogurt"
    ]


def load_class_mapping() -> Optional[List[str]]:
    if CLASS_MAP_PATH.exists():
        try:
            return json.loads(CLASS_MAP_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error loading the class map: {e}")
    return None


def _build_custom_model(num_classes: int) -> Optional[torch.nn.Module]:
    if models is None:
        return None
    try:
        try:
            model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        except Exception:
            model = models.resnet18(pretrained=True)
        for param in model.parameters():
            param.requires_grad = False
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    except Exception as e:
        print(f"Error creating the local model: {e}")
        return None


class FoodRecognitionAI:
    def __init__(self):
        self.device = "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"
        print(f"ExplainEat AI starting on device: {self.device}")

        self.food_categories = load_food_labels()
        self.custom_model = self._load_local_model()
        self.classifier = self._load_zero_shot_classifier() if not self.custom_model else None
        self.transform = self._create_transform() if torch is not None and transforms is not None else None

    def _load_local_model(self) -> Optional[torch.nn.Module]:
        if torch is None or CLASS_MAP_PATH is None or MODEL_PATH is None:
            return None
        class_names = load_class_mapping()
        if not class_names or not MODEL_PATH.exists():
            return None
        try:
            model = _build_custom_model(len(class_names))
            if model is None:
                return None
            state = torch.load(MODEL_PATH, map_location=self.device)
            model.load_state_dict(state)
            model = model.to(self.device)
            model.eval()
            self.food_categories = class_names
            print(f"Local model loaded with {len(class_names)} classes.")
            return model
        except Exception as e:
            print(f"Error loading the local model: {e}")
            return None

    def _load_zero_shot_classifier(self):
        if not HAS_TRANSFORMERS:
            return None
        try:
            return pipeline(
                "zero-shot-image-classification",
                model="openai/clip-vit-base-patch32",
                device=0 if self.device == "cuda" else -1,
            )
        except Exception as e:
            print(f"Warning: classifier could not be initialized: {e}")
            return None

    def _create_transform(self):
        if transforms is None:
            return None
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def _predict_local(self, img: Image.Image, topk: int = 1) -> List[Dict[str, object]]:
        if self.custom_model is None or self.transform is None or torch is None:
            return []
        try:
            input_tensor = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.custom_model(input_tensor)
                probabilities = torch.softmax(outputs, dim=1)[0]
                values, indices = torch.topk(probabilities, min(topk, probabilities.size(0)))

            result = []
            for score, index in zip(values.cpu().tolist(), indices.cpu().tolist()):
                label = self.food_categories[index] if index < len(self.food_categories) else 'unknown'
                result.append({
                    'name': label.title(),
                    'portion': '100 g (standard portion)',
                    'grams': 100,
                    'preparation': 'detected',
                    'confidence': round(float(score) * 100, 1),
                })
            return result
        except Exception as e:
            print(f"Error during local model prediction: {e}")
            return []

    def _predict_zero_shot(self, img: Image.Image, topk: int = 1) -> List[Dict[str, object]]:
        if self.classifier is None:
            return []
        try:
            results = self.classifier(img, self.food_categories, hypothesis_template="a photo of {}")
            output = []
            for result in results[:topk]:
                confidence = result.get('score', 0)
                if confidence > 0.05:
                    output.append({
                        'name': result.get('label', 'Unknown').title(),
                        'portion': '100 g (standard portion)',
                        'grams': 100,
                        'preparation': 'detected',
                        'confidence': round(float(confidence) * 100, 1),
                    })
            return output
        except Exception as e:
            print(f"Error during zero-shot detection: {e}")
            return []

    def recognize_from_image(self, image_path: str) -> List[Dict[str, object]]:
        # 0) Roboflow workflow (cloud, multiple items per photo) if a key is set
        meal_detector = get_meal_detector()
        if meal_detector is not None:
            try:
                detected = meal_detector.detect_from_path(image_path)
                if detected:
                    return detected
            except Exception as e:
                print(f"Roboflow detection failed, using fallback: {e}")

        # 1) YOLO object detection (multiple items per photo) if a model exists
        detector = get_food_detector()
        if detector is not None:
            try:
                detected = detector.detect_from_path(image_path)
                if detected:
                    return detected
            except Exception as e:
                print(f"YOLO detection failed, using fallback: {e}")

        # 2) Fallback: old single-label classifier / zero-shot
        try:
            img = Image.open(image_path).convert('RGB')
            detected = self._predict_local(img)
            if detected:
                return detected
            detected = self._predict_zero_shot(img)
            if detected:
                return detected
        except Exception as e:
            print(f"Error during image processing: {e}")

        return [{"name": "Meat", "portion": "100 g (standard portion)", "grams": 100, "preparation": "fallback", "confidence": 0}]

    def recognize_from_bytes(self, image_bytes: bytes) -> List[Dict[str, object]]:
        # 0) Roboflow workflow (cloud, multiple items per photo) if a key is set
        meal_detector = get_meal_detector()
        if meal_detector is not None:
            try:
                detected = meal_detector.detect_from_bytes(image_bytes)
                if detected:
                    return detected
            except Exception as e:
                print(f"Roboflow detection failed, using fallback: {e}")

        # 1) YOLO object detection (multiple items per photo) if a model exists
        detector = get_food_detector()
        if detector is not None:
            try:
                detected = detector.detect_from_bytes(image_bytes)
                if detected:
                    return detected
            except Exception as e:
                print(f"YOLO detection failed, using fallback: {e}")

        # 2) Fallback: old single-label classifier / zero-shot
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            detected = self._predict_local(img)
            if detected:
                return detected
            detected = self._predict_zero_shot(img)
            if detected:
                return detected
        except Exception as e:
            print(f"Error during image processing from bytes: {e}")

        return [{"name": "Meat", "portion": "100 g (standard portion)", "grams": 100, "preparation": "fallback", "confidence": 0}]

    def available_training_images(self) -> Dict[str, List[Path]]:
        data = {}
        image_root = TRAINING_DIR / 'images'
        if image_root.exists():
            for label_dir in sorted(image_root.iterdir()):
                if label_dir.is_dir():
                    images = [*sorted(label_dir.glob('*.jpg')), *sorted(label_dir.glob('*.png'))]
                    if images:
                        data[label_dir.name] = images
        return data


_ai_model: Optional[FoodRecognitionAI] = None


def get_food_ai() -> FoodRecognitionAI:
    global _ai_model
    if _ai_model is None:
        try:
            _ai_model = FoodRecognitionAI()
        except Exception as e:
            print(f"Error loading the AI model: {e}")
            _ai_model = None
    return _ai_model
