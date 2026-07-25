# ExplainEat – KI-Ernaehrungscoach

**KI-gestuetzte Ernaehrungsplattform – Ernaehrung verstehen, nicht nur tracken.**

ExplainEat analysiert Mahlzeiten mit KI und erklaert verstaendlich, wie sie den Koerper beeinflussen – wie ein persoenlicher Ernaehrungscoach, nicht wie eine Kalorien-Zaehler-App.

## Demo-Video / Screen Recording

Das Video zeigt die App in Aktion: [ExplainEat_Pitch_v3.mp4](ExplainEat_Pitch_v3.mp4)

---

## Funktionen

- **Mahlzeiten analysieren** – Text eingeben, KI erklaert Naehrwerte, Wirkung und Defizite
- **Tagesprotokoll** – Alle Mahlzeiten des Tages + Tageszusammenfassung
- **Einkaufsliste** – Basierend auf Ernaehrungszielen und Defiziten
- **Rezept-Generator** – Rezepte aus vorhandenen Zutaten und Zeitvorgabe
- **Personalisierung** – Profil mit Alter, Gewicht und Ziel

---

## Setup & Ausfuehren

### Voraussetzungen

- Python 3.10+
- Anthropic API Key ([anthropic.com](https://www.anthropic.com))

### Installation

```bash
# 1. Abhaengigkeiten installieren
pip install -r requirements.txt

# 2. API Key setzen
copy .env.example .env
# .env oeffnen und ANTHROPIC_API_KEY eintragen

# 3. App starten
python app.py
```

Browser oeffnen: **http://localhost:5000**

---

## Projektstruktur

```
ExplainEat/
├── app.py                   # Flask-Backend + Claude API
├── requirements.txt         # Python-Abhaengigkeiten
├── .env.example             # Vorlage fuer API-Key
├── templates/
│   └── index.html           # Frontend (HTML/CSS/JS)
├── kritische_reflexion.md   # Kritische Reflexion (Wettbewerb)
├── ExplainEat_Pitch_v3.mp4  # Demo-Video / Screen Recording
└── README.md
```

---

## Technologie-Stack

| Komponente | Technologie |
|---|---|
| Backend | Python / Flask |
| KI | Claude API (Anthropic) – claude-sonnet-5 |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Naehrwertdaten | Schaetzung via LLM |

---

## Hinweise

- Keine dauerhafte Datenspeicherung (session-basiert)
- Keine medizinischen Diagnosen
- Naehrwertangaben sind KI-Schaetzungen

---

*Entwickelt von Nik – KI Challenge 2026*
