# Amazon PPC Optimizer

Ein professionelles Streamlit-Tool für Amazon PPC Consultants zur intelligenten Optimierung von Sponsored Products Kampagnen durch datengetriebene Analyse und automatisierte Gebotsanpassungen.

## Hauptfunktionen

### 📊 **Kampagnen-Analyse & Optimierung**
- **Keyword-Performance Klassifizierung**: Automatische Bewertung von Keywords basierend auf ACOS und Conversion Rate mit konfigurierbaren UND-Bedingungen
- **Intelligente Gebotsanpassungen**: Datenbasierte Empfehlungen für Keyword-Gebote basierend auf Performance-Metriken
- **Placement-Optimierung**: Automatische Berechnung optimaler Bid-Anpassungen für verschiedene Platzierungen (Top of Search, Product Pages, Rest of Search)

### 🎯 **Flexible Konfiguration**
- **Client-spezifische Ziele**: Anpassbare Target ACOS und Mindest-Conversion-Rate
- **Markt-Strategien**: Vorkonfigurierte Settings für Market Leader und Large Inventory Clients
- **Erweiterte Parameter**: Konfigurierbare Mindest-Klicks für Keyword-Analyse

### 📈 **Umfassende Datenanalyse**
- **Suchbegriff-Analyse**: Detaillierte Auswertung der besten und schlechtesten Suchbegriffe pro Kampagne
- **Performance-Metrics**: Vollständige Anzeige von Klicks, Bestellungen, Ausgaben, Verkäufen, ACOS und Conversion Rate
- **Kampagnen-Details**: Anzeige von Kampagnennamen und Targeting-Typ für bessere Übersicht

### 🔄 **Excel Integration**
- **Bulk-Sheet Import**: Direkter Import von Amazon Bulk-Sheets (Sponsored Products-Kampagnen)
- **Automatische Spaltenerkennung**: Intelligente Erkennung und Mapping von deutschen und englischen Spaltennamen
- **Export-Funktionalität**: Export der optimierten Daten zurück in Excel-Format für direkten Upload zu Amazon

## Unterstützte Dateiformate

### Erforderliche Sheets:
- **Sponsored Products-Kampagnen**: Hauptdatenquelle für Gebotsänderungen
  - Keywords, Gebote (Max. Gebot/CPC), Performance-Daten
  - Kampagnenname, Targeting-Typ, Kampagnen-ID
  - Match Types, Klicks, Bestellungen, Ausgaben, Verkäufe, ACOS, Conversion Rate

### Optionale Sheets:
- **SP Bericht Suchbegriff**: Zusätzliche Analyse von Customer Search Terms
  - Erweiterte Suchbegriff-Performance-Analyse
  - Best/Worst Performer Identifikation

## Optimierungs-Regeln

### Keyword-Klassifizierung (UND-Logik):
- ✅ **Gut**: ACOS ≤ Target UND Conversion Rate ≥ Minimum
- ❌ **Schlecht**: ACOS > Target ODER Conversion Rate < Minimum
- 🚫 **Pausieren**: ≥25 Klicks ohne Conversions

### Placement-Anpassungen:
- **Automatische RPC-Berechnung**: Revenue per Click Optimierung
- **Target-basierte Anpassungen**: Anpassungen basierend auf Ziel-ACOS
- **Platzierungs-spezifische Strategien**: Individuelle Optimierung für jede Placement-Position

### Client-Profile:
- **Market Leader**: Target ACOS 8%, aggressive Strategie
- **Large Inventory**: Target ACOS 8%, Budget-effiziente Optimierung  
- **Standard**: Target ACOS 20%, ausgewogene Strategie

## Installation & Setup

### Voraussetzungen
- Python 3.8+
- Streamlit
- Pandas, Plotly für Datenverarbeitung und Visualisierung

### Installation
```bash
# Repository klonen
git clone [repository-url]
cd amazon-ppc-optimizer

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### Anwendung starten
```bash
streamlit run app.py
```

## Anwendung

### 1. Konfiguration
- **Client-Details eingeben**: Name, Markt-Position
- **Ziele definieren**: Target ACOS und Mindest-Conversion-Rate
- **Parameter anpassen**: Minimum Klicks für Analyse

### 2. Daten-Upload
- **Bulk-Sheet hochladen**: Amazon Excel-Export auswählen
- **Automatische Verarbeitung**: Spalten werden automatisch erkannt und gemappt
- **Vorschau prüfen**: Verarbeitete Daten vor Optimierung überprüfen

### 3. Optimierung durchführen
- **"Optimierung starten"** klicken
- **Ergebnisse analysieren**: Automatische Klassifizierung und Empfehlungen
- **Dashboard einsehen**: Detaillierte Aufschlüsselung aller Änderungen

### 4. Export & Umsetzung
- **Excel-Export**: Optimierte Daten für direkten Amazon-Upload
- **Änderungen implementieren**: Bulk-Upload der angepassten Gebote

## Dashboard-Features

### Keyword-Änderungen Tab:
- Gut/schlecht laufende Keywords pro Kampagne
- Filterung basierend auf aktueller Konfiguration
- Detaillierte Begründungen für jede Klassifizierung

### Gebotsanpassungen Tab:  
- Suchbegriff-Analyse mit Best/Worst Performern
- Kampagnenname und Targeting-Typ Anzeige
- Vollständige Performance-Metriken

### Platzierungsanpassungen Tab:
- Interaktive Target ACOS Anpassung
- RPC-basierte Optimierungsempfehlungen
- Platzierungs-spezifische Performance-Daten

## Technische Details

- **Frontend**: Streamlit mit responsivem Design
- **Datenverarbeitung**: Pandas für effiziente Excel-Manipulation
- **Visualisierung**: Plotly für interaktive Charts und Metriken
- **Architektur**: Modulare Komponenten-Struktur
- **Dateiformate**: Vollständige Excel-Kompatibilität (.xlsx)

## Erweiterte Features

### Intelligente Spaltenerkennung:
- Automatisches Mapping deutscher/englischer Begriffe
- Fallback-Strategien für verschiedene Export-Formate
- Robuste Verarbeitung verschiedener Amazon-Versionen

### Performance-Optimierung:
- Effiziente Verarbeitung großer Datensätze
- Parallele Verarbeitung von Kampagnen-Gruppen
- Optimierte Speichernutzung

### Benutzerfreundlichkeit:
- Intuitive Navigation zwischen Modulen
- Umfassende Hilfe-Texte und Tooltips
- Fehlerbehandlung mit verständlichen Meldungen

## Support & Wartung

Das Tool ist darauf ausgelegt, mit Standard Amazon Bulk-Sheets zu arbeiten und kann bei Änderungen der Amazon-API oder -Formate entsprechend angepasst werden.

---

*Entwickelt für professionelle Amazon PPC Consultants zur Steigerung der Kampagnen-Effizienz und ROI-Optimierung.* 