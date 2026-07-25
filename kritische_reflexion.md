# Kritische Reflexion – ExplainEat

---

## 1. Was war das Ziel? Habe ich es erreicht? Wie bin ich vorgegangen?

**Ziel:** Ich wollte eine App bauen, die Mahlzeiten nicht einfach nur mit Zahlen beschreibt (z.B. „500 Kalorien"), sondern erklärt, was das für eine bestimmte Person bedeutet – je nach Ziel, Gewicht und Profil.

**Erreicht:** Ja, im Kern. Man macht ein Foto, die KI erkennt die Zutaten, berechnet Nährwerte, vergibt einen Score von 0–100 und erklärt auf normaler Sprache, was passt und was fehlt. Rezeptvorschläge und Allergie-Filter funktionieren ebenfalls.

**Nicht erreicht:** Die App kann noch nicht zuverlässig schätzen, wie viel von einem Lebensmittel auf dem Teller liegt (z.B. „Reis – aber 80g oder 250g?"). Die Rezeptdatenbank ist außerdem noch klein.

**Vorgehen:**
1. Zuerst habe ich Regeln festgelegt: Was macht eine Mahlzeit für welches Profil gut oder schlecht?
2. Aus diesen Regeln habe ich automatisch 30.000 Beispiele erstellt – sogenannte **Trainingsdaten** (= Datensätze, aus denen eine KI lernt).
3. Ein **neuronales Netz** (= ein KI-Modell, das ähnlich wie ein Gehirn aus Beispielen lernt) habe ich damit trainiert, mithilfe von **PyTorch** (= eine weit verbreitete Software zum Entwickeln von KI-Modellen).
4. Zuletzt habe ich die Bilderkennung (**SAM2 über Roboflow** = ein fertiges KI-Modell, das Objekte auf Fotos erkennt) und die App-Oberfläche (mit **Flutter** = ein Werkzeug zum Bauen von Smartphone-Apps) angebunden.

---

## 2. Was ist meine Eigenleistung? Welche Hilfe habe ich genutzt? Wo habe ich KI eingesetzt?

**Selbst gemacht:**
- Konzept und Idee der App
- Die Bewertungslogik: Welche Mahlzeit bekommt welchen Score, und warum?
- Das KI-Modell: Aufbau, Training und alle Entscheidungen dazu
- Die Nährwertdatenbank mit den Zutaten
- Die Allergie-Erkennung – auch bei versteckten Allergenen (z.B. Nüsse in Pesto)
- Die Empfehlungs- und Rezeptlogik
- Die technische Verbindung aller Teile: **Flask** (= unsichtbares „Gehirn" der App im Hintergrund) und **Flutter** (= die Oberfläche, die man als Nutzer sieht)

**Fertige Hilfsmittel, die ich genutzt habe:**
PyTorch, das Roboflow-Modell, Flask, Flutter und öffentliche Nährwerttabellen – das sind frei verfügbare Werkzeuge, die ich eingebunden, aber nicht selbst entwickelt habe.

**KI beim Programmieren:** KI-Tools habe ich beim Schreiben von Code eingesetzt – für **Boilerplate-Code** (= sich wiederholende Standard-Codeblöcke), **Debugging** (= Fehler suchen und beheben) und **Refactoring** (= Code vereinfachen und aufräumen). Alle wichtigen Entscheidungen – was die App können soll und wie – habe ich selbst getroffen. Jeden von der KI generierten Code habe ich gelesen und geprüft.

---

## 3. Was funktioniert? Was funktioniert (noch) nicht?

**Funktioniert:**
- Foto → Zutaten erkennen → Nährwerte berechnen → Score und Erklärung in normaler Sprache
- Das Modell stimmt zu ~98% mit meinen selbst definierten Regeln überein
- Die App reagiert korrekt, wenn ich Profil oder Ziel ändere
- Der Allergie-Filter funktioniert zuverlässig

**Funktioniert noch nicht:**
- Mengenschätzung: Die KI erkennt „Reis", aber nicht wie viel davon auf dem Teller liegt
- Gemischte Gerichte wie Suppen oder Aufläufe werden noch schlecht erkannt
- Es gibt keine Analyse über mehrere Tage hinweg
- Die Ergebnisse wurden noch nicht von Ernährungsexperten unabhängig überprüft

---

## 4. Was kann meine KI? Was kann sie nicht?

**Was sie kann:**
- Eine Mahlzeit im Kontext einer Person bewerten – nicht nur Zahlen zeigen
- Erklären, was fehlt und warum
- Passende Rezepte vorschlagen und neue erstellen
- Allergene erkennen, auch bei Lebensmitteln, wo man es nicht vermuten würde

**Was sie nicht kann:**
- Den genauen Nährwert einer Mahlzeit bestimmen – sie schätzt nur
- Erkennen, wie groß eine Portion ist oder wie ein Gericht zubereitet wurde
- Medizinische Empfehlungen geben
- Besondere Situationen berücksichtigen, z.B. Schwangerschaft oder chronische Krankheiten
- Essstörungen erkennen oder darauf reagieren
- Ernährungswissenschaft wirklich „verstehen" – sie erkennt Muster in Daten, versteht aber keine Zusammenhänge

---

## 5. Welche Daten habe ich verwendet? Sind sie zuverlässig und fair?

**Verwendete Daten:**
- 30.000 künstlich generierte Trainingsbeispiele (automatisch aus meinen eigenen Regeln erstellt)
- Nährwerte von ~40 Grundlebensmitteln aus öffentlichen Tabellen
- ~1.000 Rezepte

**Zuverlässig?** Die Daten sind in sich stimmig – aber sie sind nicht real. Die 98% Genauigkeit bedeuten: Das Modell folgt meinen Regeln gut. Ob diese Regeln ernährungswissenschaftlich korrekt sind, wurde nicht unabhängig bestätigt.

**Mögliche Biases (= einseitige Verzerrungen in den Daten):**

- **Kultur-Bias:** Meine Datenbank und Rezepte sind größtenteils westlich geprägt. Asiatische, afrikanische oder orientalische Gerichte werden schlechter erkannt und bewertet – für Nutzer mit anderen Essgewohnheiten ist das unfair.
- **Regel-Bias:** Meine Definition von „gesund" basiert auf gängigen Ernährungsempfehlungen. Vegane, **ketogene** (= sehr kohlenhydratarme Ernährung) oder religiös bedingte Ernährungsweisen können schlechter bewertet werden, obwohl sie für die jeweilige Person vollkommen passen.
- **Körper-Bias:** Standardformeln für den Kalorienbedarf passen nicht für alle gleich gut – sehr kleine, ältere, chronisch kranke oder schwangere Personen können falsche Empfehlungen erhalten.
- **Bild-Bias:** Das Bilderkennungs-Modell (Roboflow) wurde von Dritten entwickelt und trainiert – ich hatte keinen Einfluss darauf, mit welchen Bildern es ursprünglich gelernt hat.

---

## 6. Zwei Szenarien

**a) Positive Erfahrung:**

Lea, 24, möchte Muskeln aufbauen und trainiert dreimal pro Woche – kommt aber nicht voran. Sie fotografiert ihr Mittagessen. Meine App bewertet es mit 62/100 und erklärt: „Genug Kalorien, aber zu wenig Protein für dein Ziel." Zum ersten Mal sieht sie konkret, was fehlt. Die App schlägt eine proteinreichere Alternative vor und berücksichtigt dabei automatisch ihre Nussallergie – auch im Pesto, wo Lea selbst nicht daran gedacht hätte.

**b) Negative Erfahrung / möglicher Missbrauch:**

Jonas, 17, ist unsicher mit seinem Körper und gibt ein viel zu niedriges Zielgewicht in meine App ein. Die App prüft das nicht und berechnet daraufhin einen sehr niedrigen Kalorienbedarf. Normale Mahlzeiten werden mit roten Warnungen bewertet. Aus einem Erklär-Werkzeug wird ein Kontroll-Instrument, das ungesundes Essen scheinbar „bestätigt" – mit der Autorität einer objektiven KI. Außerdem könnten Profildaten und Essensfotos als Druckmittel durch andere missbraucht werden, z.B. durch Trainer. Hinzu kommt: Essensfotos und Profildaten sind persönliche Gesundheitsdaten. Meine App bräuchte Mindestwerte beim Zielgewicht, Warnhinweise bei auffälligen Mustern und einen klaren Hinweis, dass es sich um einen Prototyp handelt – keine medizinische Beratung.
