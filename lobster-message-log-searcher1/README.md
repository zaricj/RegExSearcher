## Informationen über das Projekt
Dieses Tool dient der Auswertung von verarbeiteten Dateien innerhalb eines Lobster-Systems. Es analysiert speziell die *_message.log-Dateien im Verzeichnis Lobster_data/logs/DataWizard, um daraus Informationen zu den verarbeiteten Eingabedateien zu extrahieren.

Die Anwendung durchsucht die Log-Dateien nach allen Eingabedateien, die in den letzten 7 Tagen verarbeitet wurden. Optional können auch ältere Log-Dateien von einem Backup-Share (\\NESNAS01\ebd_archiv) hinzugezogen werden, um den Auswertungszeitraum zu erweitern.

`Zeit | Jobnummer | Profilname | Dateiname | Dateigröße in Bytes`

Zusätzlich bietet das Tool die Möglichkeit, diese CSV-Datei in eine formatierte Excel-Datei (.xlsx) umzuwandeln

## Anforderungen
Python Version:

- **Python 3.12.x+**

Die folgenden Python-Pakete:

- pandas
- PySide6
- XlsxWriter

Die aufgeführten Pakete können über die Datei **requirements.txt** installiert werden.

Um die Pakete zu installieren, CMD/Terminal öffnen in diesem Projekt und mit folgendem Befehl die Pakete installieren:

```bash
pip install -r requirements.txt
```

## Screenshot des Programms
![alt text](/img/program_screenshot.png)

