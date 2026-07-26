# Kritische Reflexion — ExplainEat

**Projekt:** ExplainEat — erklärbare, personalisierte Ernährungs-KI  
**Eingereicht von:** Nik · Schweizer KI Challenge 2026

## 1. Ziel des Projekts, Zielerreichung und Vorgehen
Ziel. Eine App, die Ernährung nicht nur misst, sondern auch erklärt und personalisiert. Sie soll Lebensmittel auf einem Foto erkennen, eine Mahlzeit anhand eines individuellen Profils bewerten und passende Rezepte vorschlagen oder selbst zusammenstellen. Zum Profil gehören beispielsweise das Körpergewicht, das persönliche Ziel, die körperliche Aktivität und mögliche Allergien.

Zielerreichung. Das Ziel wurde weitgehend erreicht. Es gibt eine funktionsfähige Web-App mit Flutter und einem Python-/Flask-Backend. Die App verfügt über eine Fotoerkennung, eine personalisierte Bewertung mit verständlicher Erklärung, rund 1’000 Rezepte, KI-basierte Empfehlungen und eine KI-gestützte Rezeptgenerierung mit einer an das Körpergewicht angepassten Einkaufsliste.

Noch nicht erreicht ist eine nötige Genauigkeit, sowie eine präzise Schätzung der Mengen auf einem Foto. Diese Einschränkungen werden in den Abschnitten 3 und 4 genauer beschrieben.

Vorgehen / KI-Technologien. ExplainEat verwendet zwei KI-Bausteine:

(a) Ein eigenes neuronales Netz, das mit PyTorch (Open-Source-Framework für maschinelles Lernen und Deep Learning) entwickelt wurde. Dabei handelt es sich um ein mehrschichtiges Perzeptron. Als Eingaben verwendet das Modell Informationen aus dem persönlichen Profil und die Makronährwerte einer Mahlzeit. Als Ausgaben erzeugt es einen Score zwischen 0 und 100, vier Hinweise zu Protein, Ballaststoffen, Zucker und Kalorien sowie eine Empfehlungsklasse.

(b) Eine Bilderkennung mit einem vortrainierten Open-Vocabulary-Segmentierungsmodell. Dieses ist über einen Roboflow-Workflow eingebunden und kann mehrere Zutaten auf einem Foto erkennen.

Das System ExplainEat besteht aus folgenden Bausteinen:

- **Bildanalyse** — Erkennung und Segmentierung der Mahlzeit mit Roboflow und SAM2.
- **Daten- und Wissensbasis** — Nährwerte, Rezepte, Allergene, Profile und Bewertungsregeln.
- **PyTorch-KI-Modell** — Bildung des Feature Vectors, Training und Berechnung des personalisierten Scores.
- **Erklärung und Empfehlungen** — Verständliche Auswertung, Verbesserungen und Rezeptvorschläge.
- **Orchestrierung und Schnittstellen** — Verbindung aller Komponenten über Flask, REST/JSON und die Flutter-App.

ExplainEat ist recht umfangreich geworden. Deshalb habe ich mir erlaubt, zusätzlich eine Projektdokumentation beizulegen, die detaillierte Erläuterungen zu den Bausteinen und zu der Integration und den Schnittstellen liefert.

## 2. Eigenleistung, Hilfsmittel und KI-Einsatz
Eigenleistung. Zu meiner Eigenleistung gehören die Entwicklung des Konzepts, die Planung der Nutzerführung und die Gestaltung der Anwendung. Ein besonderer Schwerpunkt lag auf der Auswahl und dem Aufbau des eigenen neuronalen Netzes. Dazu gehörten die Architektur, die Codierung der Merkmale und die Trainingsstrategie.

Zusätzlich entwickelte ich die Bewertungslogik und legte die Zielwerte fest. Darauf basiert die Nährwertdatenbank und die Rezeptdaten. Ausserdem integrierte ich den mehrstufigen Workflow für die Bilderkennung, führte Tests durch und die Fehlersuche/Bereinigung.

Besonders anspruchsvoll war die Verbindung des PyTorch-Modells mit dem Python-/Flask-Backend und dem Flutter-Frontend. Dadurch mussten verschiedene Technologien und Datenformate miteinander verbunden werden.

Genutzte Hilfe. Als Programmierunterstützung verwendete ich das KI-Coding-Tool Claude. Das Tool half dabei, anhand meiner Vorgaben Programmcode zu schreiben, Fehler zu finden und mögliche Lösungen vorzuschlagen.

Die Entscheidungen über die Architektur, die Funktionen und die Bewertungslogik wurden jedoch von mir getroffen. Auch die Ergebnisse wurde von mir akribisch überprüft und angepasst. Der von Claude erstellte Code habe ich nicht ungeprüft übernommen.

Wo KI im Produkt steckt.

(1) Das selbst trainierte neuronale Netz von ExplainEat bewertet die Mahlzeiten. Es erzeugt den Score, die Hinweise zu einzelnen Nährwerten und eine Empfehlungsklasse. Die Ergebnisse werden ausserdem für die Auswahl und Zusammenstellung passender Rezepte verwendet.

(2) Das Segmentierungsmodell übernimmt die Bilderkennung und erkennt mehrere Lebensmittel oder Zutaten auf einem Foto.

Für die zentrale Ernährungsbewertung wurde bewusst keine fertige Sprach-KI verwendet. Stattdessen wurde ein eigenes Modell trainiert, damit dessen Aufbau, Eingaben und Ausgaben besser verstanden und erklärt werden können.

## 3. Was funktioniert — und was (noch) nicht
Funktioniert: Die Anwendung kann auf einem Foto mehrere einzelne Zutaten erkennen. Anschliessend bewertet sie die Mahlzeit anhand des persönlichen Profils und erklärt verständlich, weshalb die Mahlzeit gut oder weniger gut zum gewählten Ziel passt.

Die App enthält rund 1’000 durchsuchbare Rezepte. Die KI-Empfehlungen unterscheiden sich je nach Profil. Bei einem Profil mit dem Ziel Muskelaufbau werden beispielsweise eher proteinreiche Gerichte vorgeschlagen. Bei einem Profil mit dem Ziel Abnehmen werden eher leichtere Gerichte empfohlen.

Weitere funktionierende Bestandteile sind:

- KI-gestützte Rezeptvorschläge
- eine an das Körpergewicht angepasste Einkaufsliste
- Hinweise auf mögliche Nährstoffdefizite
- ein Allergie-Filter, der ungeeignete Rezepte ausblendet
Funktioniert (noch) nicht gut: Die Mengenschätzung auf einem Foto ist noch ungenau. Sie wird momentan hauptsächlich aus der Grösse des erkannten Bereichs auf dem Bild abgeleitet. Ein grosser Bereich auf einem Foto bedeutet jedoch nicht automatisch, dass das Lebensmittel auch ein hohes Gewicht besitzt.

Die Nährwertdatenbank umfasst momentan nur ungefähr 40 Lebensmittel. Bei unbekannten Zutaten greift das System deshalb auf Standard- oder Ersatzwerte zurück. Dadurch kann die Bewertung ungenau werden.

Die Erklärungstexte werden aus den Ergebnissen des Modells und aus vorbereiteten Textbausteinen zusammengesetzt. Sie werden nicht vollständig frei durch eine Sprach-KI formuliert.

Das eigene neuronale Netz lernt aus synthetischen, regelbasierten Trainingsdaten. Es kann die darin enthaltenen Ernährungsregeln gut wiedergeben, wurde bisher aber noch nicht mit genügend echten Daten oder «medizinisch» geprüften Ergebnissen verglichen.

Auch der Login ist bisher nur sehr einfach umgesetzt und deshalb nicht für eine produktive Anwendung mit echten persönlichen Daten geeignet. (Prototyp)

## 4. Was die KI kann — und was nicht
Kann: Die KI kann eine Mahlzeit für ein bestimmtes Profil bewerten und dazu einen Score sowie eine Begründung ausgeben. Sie kann mögliche Defizite bei Protein oder Ballaststoffen erkennen und auf hohe Werte bei Zucker oder Kalorien hinweisen.

Ausserdem kann sie eine sinnvolle Lebensmittel- oder Rezeptkategorie empfehlen, aus rund 1’000 Rezepten passende Vorschläge auswählen und neue Rezeptvorschläge zusammenstellen. Dabei können das Körpergewicht, das persönliche Ziel und angegebene Allergien berücksichtigt werden.

Die Bilderkennung kann mehrere Zutaten auf einem Foto erkennen.

Kann nicht: Die KI kann keine medizinisch verlässliche oder therapeutische Beratung leisten. Sie kann Erkrankungen wie Diabetes, Stoffwechselstörungen oder Essstörungen nicht sicher berücksichtigen.

Auch versteckte Allergene können nicht vollständig erkannt werden. Besonders bei verarbeiteten oder unbekannten Produkten ist häufig nicht sichtbar, welche Zutaten tatsächlich enthalten sind.

Die KI kann ausserdem keine exakten Grammangaben aus einem Foto bestimmen, keine beliebigen Fragen in natürlicher Sprache verstehen und die Korrektheit ihrer Ergebnisse nicht garantieren.

ExplainEat ist deshalb ein Hilfsmittel zur Orientierung und zum Lernen. Die Anwendung ist kein Ersatz für eine medizinische oder professionelle Ernährungsberatung.

## 5. Daten: Zuverlässigkeit, Fairness, Bias
Verwendete Daten.

(a) Synthetische Trainingsdaten mit rund 30’000 künstlich erstellten Kombinationen aus persönlichen Profilen und Mahlzeiten. Die dazugehörigen Bewertungen wurden anhand allgemeiner Ernährungsregeln erzeugt. Dazu gehören beispielsweise der ungefähre Proteinbedarf pro Kilogramm Körpergewicht und eine grobe Berechnung des Kalorienbedarfs.

(b) Eine kleine Nährwertdatenbank mit typischen Durchschnittswerten pro 100 Gramm eines Lebensmittels.

(c) Rund 1’000 Rezepte, die überwiegend programmatisch aus echten und üblichen Zutatenkombinationen zusammengestellt wurden.

Zuverlässigkeit. Für einen Prototyp sind die verwendeten Daten brauchbar. Die Bewertungen beruhen jedoch hauptsächlich auf allgemeinen Empfehlungen und Faustregeln. Sie wurden nicht durch eigene klinische Studien bestätigt.

Auch die gespeicherten Nährwerte sind nur Durchschnittswerte. Die tatsächlichen Werte können sich je nach Produkt, Herkunft, Zubereitungsart und Portionsgrösse unterscheiden.

Fairness / Bias (ehrlich):

Demografischer Bias: Die verwendeten Zielwerte orientieren sich an Durchschnittswerten der Bevölkerung. Unterschiede beim Alter, Geschlecht, bei Schwangerschaft, Erkrankungen oder Leistungssport werden nicht ausreichend berücksichtigt. Für diese Personengruppen können die Empfehlungen deshalb unpassend sein.

Körperbau-Bias: Die Skalierung der Portionen verwendet hauptsächlich das Körpergewicht. Sie unterscheidet nicht genau zwischen Muskelmasse, Körperfett, Knochenmasse und Wasseranteil. Dadurch können Portionen über- oder unterschätzt werden.

Kultureller Bias: Die erkennbaren Lebensmittel, die Rezepte und die Nährwertdatenbank sind hauptsächlich westlich und europäisch geprägt. Gerichte aus anderen Kulturen und Regionen werden möglicherweise schlechter erkannt oder nicht passend bewertet.

Sicherheits-Grenze: Der Allergie-Filter erkennt inzwischen auch einige versteckte Allergene über Kategorien. So kann das System beispielsweise erkennen, dass Pesto Nüsse, Tzatziki Milchprodukte und Mayonnaise Ei enthalten kann.

Der Filter arbeitet jedoch weiterhin hauptsächlich mit Schlüsselwörtern und Kategorien. Er kann nicht jedes verarbeitete oder unbekannte Produkt korrekt beurteilen. Deshalb ist er keine medizinische Garantie und darf die eigene Kontrolle der Zutatenliste nicht ersetzen.

## 6. Zwei kurze Szenarien
a. Positiv. Lena wiegt 68 Kilogramm und hat das Ziel, Muskeln aufzubauen. Sie fotografiert ihr Mittagessen mit ExplainEat.

Die App erkennt Reis und Gemüse und bewertet die Mahlzeit mit 55 von 100 Punkten. ExplainEat erklärt, dass die Mahlzeit zwar Kohlenhydrate und Gemüse enthält, für das Ziel Muskelaufbau jedoch eine ausreichende Proteinquelle fehlt.

Anschliessend empfiehlt die KI ein proteinreicheres Rezept und erstellt eine Einkaufsliste, deren Mengen an Lenas Körpergewicht angepasst sind.

Lena erhält dadurch nicht nur eine Empfehlung, sondern versteht auch, weshalb die ursprüngliche Mahlzeit nicht optimal zu ihrem Ziel passt. Sie kann dieses Wissen später selbst anwenden.

b. Negativ / Missbrauch. Eine Person mit einem problematischen Essverhalten könnte den Kalorien-Score und die Empfehlungen für leichtere Gerichte verwenden, um extreme Einschränkungen zu rechtfertigen. Die Anwendung könnte dadurch unbeabsichtigt ein ungesundes Verhalten verstärken.

Auch beim Allergie-Filter bleibt ein Restrisiko. Häufige versteckte Allergene werden zwar berücksichtigt, ein unbekanntes oder stark verarbeitetes Produkt ausserhalb der gespeicherten Schlüsselwortliste könnte jedoch falsch eingeordnet werden. Dadurch könnte bei der betroffenen Person eine falsche Sicherheit entstehen.

Die Konsequenz daraus ist, dass die App klare Hinweise benötigt:

- ExplainEat bietet keine medizinische Beratung.
- Allergien müssen immer zusätzlich anhand der Zutatenliste geprüft werden.
- Bei gesundheitlichen Problemen muss eine Fachperson kontaktiert werden.
- Für einen praktischen Einsatz wäre eine professionell geprüfte Allergen-Datenbank notwendig.
