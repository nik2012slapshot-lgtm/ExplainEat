# ExplainEat Trainingsdaten und Modelltraining

## Welche Erkennung nutzt die App?

Für Foto-Uploads probiert `recognize_food(...)` die Erkenner in dieser
Reihenfolge (jeweils mit stillem Fallback auf den nächsten):

1. **Roboflow-Workflow „Meal Ingredient Boxes" (Cloud, SAM3)** — erkennt
   **mehrere Zutaten pro Foto**. Aktiv, sobald `ROBOFLOW_API_KEY` gesetzt ist
   (siehe README, Abschnitt „Bilderkennung mehrerer Zutaten"). Kein lokales
   Training nötig — neue Klassen pflegst du direkt im Roboflow-Workflow.
2. **Lokales YOLO-Modell** (`explain_eat/models/food_detector.pt`) — optional,
   per `scripts/train_yolo.py` trainiert (siehe
   `explain_eat/training/yolo/README_YOLO.md`).
3. **Lokaler ResNet-Klassifikator** — das unten beschriebene Single-Label-Modell
   (genau **eine** Klasse pro Foto). Dient als letzter Fallback.

Die folgenden Abschnitte betreffen Variante 3 (das lokale ResNet-Training).

## Ordnerstruktur

Lege deine Trainingsdaten wie folgt ab – relativ zum Projektstamm `C:\Users\timfe\ExplainEat`:

- `C:\Users\timfe\ExplainEat\explain_eat\training\food_labels.txt`
- `C:\Users\timfe\ExplainEat\explain_eat\training\images\<label>\*.jpg` oder `*.png`

Beispiel:

- `C:\Users\timfe\ExplainEat\explain_eat\training\images\salad\`
- `C:\Users\timfe\ExplainEat\explain_eat\training\images\chicken\`
- `C:\Users\timfe\ExplainEat\explain_eat\training\images\fruit\`

Die Ordnernamen müssen exakt den Labels in `food_labels.txt` entsprechen.

## Label-Datei

Erstelle oder ergänze `explain_eat/training/food_labels.txt` mit einer Kategorie pro Zeile:

```
bread
vegetable
fruit
meat
fish
salad
chicken
pizza
apple
banana
```

Wenn die Datei existiert, wird sie vom Training und von der KI-Auswertung verwendet.

## Konkretes Beispiel

Angenommen, du möchtest drei Klassen trainieren: `chicken`, `salad` und `apple`.

### Datei `explain_eat/training/food_labels.txt`

```
chicken
salad
apple
```

### Ordner für Bilder

- `explain_eat/training/images/chicken/`
- `explain_eat/training/images/salad/`
- `explain_eat/training/images/apple/`

### Beispielhafte Bilddateien

- `explain_eat/training/images/chicken/chicken_01.jpg`
- `explain_eat/training/images/chicken/chicken_02.png`
- `explain_eat/training/images/salad/salad_01.jpg`
- `explain_eat/training/images/salad/salad_02.png`
- `explain_eat/training/images/apple/apple_01.jpg`
- `explain_eat/training/images/apple/apple_02.png`

Die Ordnernamen müssen exakt mit den Labels in `food_labels.txt` übereinstimmen.

## Modelltraining starten

Im Projektordner kannst du das Training lokal starten mit:

```powershell
python scripts/train_classifier.py --data explain_eat/training/images --labels explain_eat/training/food_labels.txt --output explain_eat/models/food_classifier.pth --classes-output explain_eat/models/food_classes.json --metrics-output explain_eat/models/metrics.json --epochs 8 --batch-size 24 --img-size 224
```

## Was das Skript macht

- Lädt alle Bilder aus `explain_eat/training/images/`
- Trainiert ein kleines ResNet-Modell für deine Labels
- Speichert das Modell in `explain_eat/models/food_classifier.pth`
- Speichert die Klassenliste in `explain_eat/models/food_classes.json`
- Speichert Trainingsmetriken in `explain_eat/models/metrics.json`

## Backend-Integration

Das Backend bietet jetzt folgende Endpunkte:

- `GET /training/status` — zeigt verfügbare Labels, Bildanzahl und Modellstatus
- `POST /training/retrain` — startet das Training asynchron im Hintergrund

Das Frontend bietet eine Schaltfläche zum Nachtrainieren in den Einstellungen.

## Bildupload für Training

Füge neue Trainingsbilder ein in:

- `explain_eat/training/images/<label>/`

Je mehr Bilder pro Label, desto robuster wird die Klassifikation.

## Automatisches Training

Für häufigere, automatische Trainingläufe kannst du einen Windows-Task anlegen oder den Backend-Endpunkt `POST /training/retrain` regelmäßig aufrufen.
