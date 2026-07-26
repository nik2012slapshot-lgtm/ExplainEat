# Abgabe-Übersicht

## Die vier Bestandteile der Abgabe

| Geforderter Bestandteil | Wo er zu finden ist |
|---|---|
| Ausführbarer Code mit README | Dieses Repository, Startanleitung in `README.md` |
| 2-minütiger Video-Pitch | `ExplainEat_Pitch_v4.mp4` |
| Kritische Reflexion | Teil 1 dieses Dokuments, im Repository als `kritische_reflexion.md` |
| Offenlegung von Quellen und Unterstützung | Teil 2, Abschnitt 3, sowie Abschnitt 10 (Quellen) |

Ergänzend liegt ein Screen Recording der laufenden App bei (`ExplainEat_App_Demo.mp4`),
damit der Ablauf auch ohne lokale Installation nachvollziehbar ist.

## Was ExplainEat macht

ExplainEat erkennt Bestandteile einer Mahlzeit auf einem Foto, lässt unsichere
Angaben vom Nutzer bestätigen, ergänzt Nährwerte, bildet daraus einen festen
numerischen Feature-Vektor, berechnet mit einem **selbst trainierten
PyTorch-Modell** einen personalisierten Score und erklärt das bereits geprüfte
Ergebnis in verständlicher Sprache.

Der technische Schwerpunkt liegt bewusst auf dem eigenen Machine-Learning-Prozess
— Datengenerierung, Feature-Design, Training, Evaluation und Integration — und
nicht auf dem visuellen Design der Oberfläche.

## Kennzahlen des eigenen KI-Modells

Alle Werte stammen aus einem reproduzierbaren Lauf auf einem **unabhängigen
Testanteil** (4 500 Beispiele), der bis zur Schlussauswertung unberührt blieb.

| Messgrösse | Wert | Was sie aussagt |
|---|---|---|
| Empfehlungsklasse (Accuracy) | 98,4 % | Trefferquote über 4 Klassen — hierauf bezieht sich die oft genannte Zahl „98 %" |
| Flag-Genauigkeit | 97,5 % | 4 binäre Hinweise (Protein, Ballaststoffe, Zucker, Kalorien) |
| Score MAE | 7,96 Punkte | Mittlerer Fehler auf der Skala 0–100 |
| Score R² | 0,758 | Erklärte Varianz |
| Toleranzquote ±5 Punkte | 37,8 % | Anteil der Scores nahe am Zielwert |

**Vergleich mit Baselines auf demselben Testanteil:**

| Verfahren | MAE | R² |
|---|---|---|
| Eigenes neuronales Netz | 7,96 | 0,758 |
| Lineare Regression | 10,26 | 0,599 |
| Konstante Vorhersage (Mittelwert) | 16,49 | −0,000 |
| Regel-Engine | 0,00 | 1,000 |

Reproduzierbar mit:

```
python scripts/train_ai_model.py --samples 30000 --epochs 40 --seed 42
python scripts/evaluate_model.py --samples 30000 --seed 42
```

## Ehrliche Einordnung dieser Zahlen

Drei Punkte sind für eine faire Beurteilung wichtig:

**Die „98 Prozent" betreffen nur die Empfehlungsklasse.** Sie sagen aus, wie
zuverlässig das Modell eine von vier Kategorien vorschlägt. Sie sind weder die
Genauigkeit des Scores noch eine Aussage über ernährungswissenschaftliche
Richtigkeit.

**Der Score selbst ist deutlich ungenauer.** Bei einem mittleren Fehler von rund
8 Punkten und einer Toleranzquote von 37,8 Prozent innerhalb von ±5 Punkten ist
er eine grobe Einordnung, kein präziser Messwert.

**Die Regel-Engine erreicht per Konstruktion einen Fehler von null**, weil sie die
Zielwerte selbst erzeugt. Das neuronale Netz ist damit ein Surrogatmodell: Es
lernt, meine eigenen Regeln nachzubilden. Dass es die linearen und konstanten
Baselines klar schlägt, belegt die technische Umsetzung und eine sinnvolle
Architekturwahl — es belegt nicht, dass die zugrunde liegenden Regeln fachlich
korrekt sind. Der nächste inhaltliche Schritt sind fachlich geprüfte Zielwerte,
nicht ein grösseres Netz.

## Grenzen des Prototyps

- Keine medizinische Beratung, keine Diagnose, keine Therapieempfehlung
- Mengenschätzung aus dem Foto ist ungenau
- Nährwertdatenbank umfasst rund 40 Grundlebensmittel
- Der Allergie-Filter arbeitet mit Schlüsselwörtern und Kategorien und ersetzt
  die eigene Kontrolle der Zutatenliste nicht
- Trainingsdaten sind synthetisch und regelbasiert, nicht fachlich validiert
