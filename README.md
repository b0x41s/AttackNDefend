# Cyber Attack & Defend 🚨💾

![Cyber Attack & Defend Banner](https://img.shields.io/badge/Cyber%20Attack%20&%20Defend-Hack%20or%20Be%20Hacked-red?style=for-the-badge&logo=shield)

> **"Test je vaardigheden in een epische strijd tussen aanval en verdediging!"**

Welkom bij **Cyber Attack & Defend**, een interactief cybersecurity-spel waar jij het opneemt tegen een slimme AI. Hack de tegenstander, verdedig je eigen systeem, en scoor punten door "flags" te stelen. Deze applicatie combineert Flask, Docker, SSH, en real-time SocketIO voor een dynamische leerervaring.

---

## 🎮 Overzicht

| **Speler** | **VS** | **AI** |
|------------|--------|--------|
| Poort: 5001 | | Poort: 5002 |
| SSH: 2222   | | SSH: 2223   |
| Hack of verdedig! | | Automatische exploits |

- **Doel**: Steel de flag van je tegenstander en bescherm die van jou.
- **Technologie**: Flask, SQLite, Docker, SocketIO.
- **Kwetsbaarheden**: SQL-injectie, onveilige authenticatie (opzettelijk!).

---

## 🚀 Snel van start

1. **Clone de repository**:
   ```bash
   git clone https://github.com/jouwgebruikersnaam/cyber-attack-defend.git
   cd cyber-attack-defend
   ```
   
Bouw de Docker-images:
```
docker build -t cyber-game-target ./target
docker build -t cyber-game-manager ./manager
```

Start de game manager: 
./start.sh 
Open de interface: 
Bezoek http://localhost:5000 in je browser. 
Verbind via SSH: ssh root@localhost -p 2222 (speler) of -p 2223 (AI). 
🎨 Visualisatie 

Hier is een overzicht van hoe het spel werkt:

mermaid

Collapse

Wrap

Copy
graph TD
    A[Speler Container<br>Poort: 5001<br>SSH: 2222] -->|Hackt| B[AI Container<br>Poort: 5002<br>SSH: 2223]
    B -->|Hackt| A
    C[Game Manager<br>Poort: 5000] -->|Beheert| A
    C -->|Beheert| B
    A -->|Flags| D[Score: Speler]
    B -->|Flags| E[Score: AI]
    C -->|Real-time Updates| F[Webinterface]
✨ Kenmerken


✨ Kenmerken
Real-time gameplay: Scores en logs worden live bijgewerkt via SocketIO.
Code-editor: Pas je applicatie aan en herbouw je container om te verdedigen.
AI-tegenstander: Probeert automatisch SQL-injecties zoals ' OR 1=1 --.
Punten:
Flag stelen: +50
Health check OK: +5
Health check mislukt: -10
🛠 Vereisten
Docker
Git
Python 3.9 (voor lokale ontwikkeling)
 

📖 Hoe te spelen
Start het spel via de webinterface.
Val aan: Gebruik de website (bijv. http://localhost:5002) of SSH om de AI-flag te stelen.
Verd```markdown Verdedig: Wijzig je broncode via de editor en herbouw je container.
Dien flags in: Voer gestolen flags in om punten te scoren.

---

## 📸 Screenshots

*(Voeg hier screenshots toe als je die hebt, bijvoorbeeld van de webinterface of een terminal-output. Je kunt deze later uploaden naar GitHub en de links hier toevoegen, zoals:)*
```markdown
![Webinterface](https://via.placeholder.com/600x300.png?text=Webinterface)
![SSH Login](https://via.placeholder.com/600x300.png?text=SSH+Login)
🤝 Bijdragen
Wil je meebouwen? Fork deze repo en stuur een pull request! Issues en suggesties zijn ook welkom.

📜 Licentie
Dit project is gelicentieerd onder de .

Gemaakt door: B0x41S | Datum: 26 maart 2025

---

### Uitleg over de "vette visualisatie"
1. **Mermaid-diagram**: Dit is een coole feature in GitHub Markdown. Het genereert een flowchart die de relatie tussen de speler, AI, en game manager visualiseert. GitHub rendert dit automatisch als een diagram.
2. **Badges**: Kleurrijke shields.io-badges geven een moderne look.
3. **Emoji's**: Voor een speelse en aantrekkelijke vibe.
4. **Structuur**: Duidelijke secties met codeblokken en tabellen maken het leesbaar en professioneel.

### Hoe te gebruiken
1. Kopieer deze Markdown-tekst naar een bestand genaamd `README.md` in je directory.
2. Vervang `jouwgebruikersnaam` door je GitHub-gebruikersnaam.
3. Upload het naar GitHub zoals eerder beschreven:
   ```bash
   git add README.md
   git commit -m "Voeg coole README toe"
   git push
