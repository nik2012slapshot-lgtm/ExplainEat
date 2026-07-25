# ExplainEat Flutter

Flutter-Frontend für ExplainEat, das sich mit einem Python-Backend verbindet.

## Voraussetzungen

- Flutter SDK installiert und im PATH
- VS Code mit Flutter-Plugin
- Python-Backend im Hauptverzeichnis

## Backend starten

Installiere Python-Abhängigkeiten:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python backend.py
```

Das Backend läuft dann standardmäßig auf `http://0.0.0.0:5000`.

## Flutter-App starten

Öffne den Ordner `flutter_app` in VS Code und führe im Terminal aus:

```bash
flutter pub get
flutter run
```

Für den Android-Emulator oder ein reales Gerät verwende als Backend-URL in der App `http://10.0.2.2:5000` für den Emulator oder die lokale IP deines Rechners für ein echtes Gerät.
