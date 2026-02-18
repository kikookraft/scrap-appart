# SeLoger Scraper

Scraper d'annonces immobilières SeLoger avec authentification par cookies et contournement anti-bot DataDome.

## Architecture

```
scrap.py                          # Scraper principal (requests + lxml)
enrich_annonces.py                # Enrichissement des annonces avec détails
extract_cookies_selenium.py       # Extracteur de cookies (Selenium + Chrome)
.cookies                          # Cookies au format JSON simple
annonces.json                     # Résultats de scraping basiques
annonces_enriched.json            # Résultats enrichis avec tous les détails
webview/                          # Interface web de visualisation
  ├── index.html                  # Page principale
  ├── style.css                   # Styles
  ├── app.js                      # Logique JavaScript
  ├── server.py                   # Serveur web Python
  ├── README_WEBVIEW.md           # Documentation du visualiseur
  ├── annonces.json               # Copie des annonces (auto-générée)
  └── annonces_enriched.json      # Copie des annonces enrichies (auto-générée)
```

## Installation

```bash
pip install -r requirements.txt
```

**Dépendances:**
- `requests` (2.31.0+) - HTTP client
- `lxml` (4.9.0+) - Parser HTML/XPath
- `selenium` (4.38.0+) - Automation navigateur
- `webdriver-manager` (4.0.1+) - Gestion ChromeDriver automatique

## Extraction des cookies

```bash
python3 extract_cookies_selenium.py
```

**Processus:**
1. Lance Chrome avec options anti-détection
2. Ouvre SeLoger.com
3. Attend que l'utilisateur navigue et se connecte manuellement
4. Appuyer sur ENTRÉE dans le terminal
5. Extrait tous les cookies automatiquement
6. Sauvegarde dans `.cookies` (format simple) et `.cookies.full` (format complet)

**Cookies critiques:**
- `datadome` - Protection anti-bot (expire rapidement)
- `visitId` - Session utilisateur
- `_ga`, `_gid` - Google Analytics

**Durée de vie:** < 1 heure (recommandé: extraire juste avant scraping)

## Scraping

```bash
python3 scrap.py                  # 1 page (~27 annonces)
python3 scrap.py --max-pages 5    # 5 pages (~135+ annonces)
```

**Filtres par défaut:**
- Prix: max 1500€
- Surface: min 65m²
- Chambres: min 3
- Villes: Lyon (690123) + Tassin-la-Demi-Lune (690244)
- Type: Location d'appartements/maisons

**URL générée:**
```
https://www.seloger.com/list.htm?projects=1&types=1,2&places=[{ci:690123},{ci:690244}]&price=NaN/1500&surface=65/NaN&bedrooms=3
```

**Options CLI:**
```bash
python3 scrap.py --url "https://..."        # URL personnalisée
python3 scrap.py --output results.json      # Fichier sortie
python3 scrap.py --max-pages 10             # Nombre de pages
python3 scrap.py --max-pages 3 --output appartements_lyon.json
```

**Pagination:**
- SeLoger limite à ~27 annonces par page
- Paramètre: `&LISTING-LISTpg=2` pour page 2
- Déduplication automatique par URL
- Délai 3-5s entre pages (anti-bot)
- Réindexation des IDs (1, 2, 3...)

## Techniques anti-bot

**Headers réalistes:**
```python
User-Agent: Mozilla/5.0 Chrome/131.0.0.0
Accept-Encoding: gzip, deflate, br, zstd
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
```

**Comportement humain:**
1. Visite page d'accueil (`/`)
2. Délai aléatoire 1.5-3s
3. Navigation vers recherche avec `Referer` header
4. Délai aléatoire 2-4s entre requêtes

**Session persistante:** Conservation des cookies via `requests.Session()`

## Enrichissement des annonces

Une fois les annonces récupérées avec `scrap.py`, utilisez `enrich_annonces.py` pour obtenir tous les détails:

```bash
# Enrichir les annonces du fichier annonces.json
python3 enrich_annonces.py

# Avec options personnalisées
python3 enrich_annonces.py --input annonces.json --output annonces_enriched.json

# Tester sur les 5 premières annonces
python3 enrich_annonces.py --limit 5
```

**Informations ajoutées:**
- 📍 **GPS**: Latitude et longitude (coordonnées précises)
- 🏙️ **Localisation nettoyée**: Ville et quartier extraits proprement
- ⚡ **DPE**: Diagnostic de Performance Énergétique (A-G)
- 🌍 **GES**: Émissions de Gaz à Effet de Serre (A-G)
- 🖼️ **Images**: URLs de toutes les photos de l'annonce
- 📐 **Surface nettoyée**: Extraction numérique (float) de la surface en m²
- 📅 **Date de récupération**: Timestamp ISO 8601 de l'enrichissement
- 📅 **Date de publication**: Date de mise en ligne de l'annonce

**Options CLI:**
```bash
python3 enrich_annonces.py --input annonces.json        # Fichier d'entrée
python3 enrich_annonces.py --output enriched.json       # Fichier de sortie
python3 enrich_annonces.py --cookies .cookies           # Fichier de cookies
python3 enrich_annonces.py --limit 10                   # Limiter pour tests
```

**Format de sortie (annonces_enriched.json):**
```json
[
  {
    "id": 1,
    "url": "https://www.seloger.com/annonces/locations/...",
    "title": "Appartement meublé",
    "price": "500 €",
    "location": "Lyon 8ème (69008)",
    "surface": "105 m²",
    "bedrooms": "3 chambres",
    "gps_latitude": 45.7640,
    "gps_longitude": 4.8357,
    "ville": "Lyon 8ème",
    "quartier": "Monplaisir",
    "dpe": "C",
    "ges": "B",
    "images": [
      "https://v.seloger.com/s/crop/590x330/...",
      "https://v.seloger.com/s/crop/590x330/..."
    ],
    "surface_clean": 105.0,
    "date_recuperation": "2026-02-17T14:30:00",
    "date_publication": "2026-02-10"
  }
]
```

**Workflow complet:**
```bash
# 1. Extraire les cookies (valides < 1h)
python3 extract_cookies_selenium.py

# 2. Scraper les annonces (données basiques)
python3 scrap.py --max-pages 5 --output annonces.json

# 3. Enrichir avec détails complets
python3 enrich_annonces.py --input annonces.json --output annonces_enriched.json

# 4. Copier les annonces dans le dossier webview
cp annonces.json annonces_enriched.json webview/

# 5. Lancer le visualiseur web
cd webview && python3 server.py
# Puis ouvrir http://localhost:8000 dans le navigateur
```

**Performance:**
- Délai: 2-4s entre chaque annonce (anti-bot)
- Durée: ~3min pour 50 annonces
- Statistiques affichées en fin de traitement

## XPath Selectors (Mis à jour 2026)

SeLoger change régulièrement sa structure HTML. Sélecteurs actuels:

```python
# Conteneurs d'annonces
"//div[@data-testid='sl.explore.card-container']"

# URL de l'annonce
".//a[@data-testid='sl.explore.coveringLink']/@href"

# Prix
".//div[@data-testid='sl.explore-card-price']//text()"

# Textes: titre, localisation, surface, chambres
".//text()"  # Filtrage par patterns (m², chambres, codes postaux)
```

**Si 0 résultats:**
1. Vérifier cookies valides et récents
2. Inspecter HTML sauvegardé
3. Identifier nouveaux `data-testid` dans le DOM
4. Mettre à jour XPath dans `_parse_listings()`

## Format de sortie (annonces.json)

```json
[
  {
    "id": 1,
    "url": "https://www.seloger.com/annonces/locations/...",
    "title": "Appartement meublé",
    "price": "500 €",
    "location": "Lyon 8ème (69008)",
    "surface": "105 m²",
    "bedrooms": "3 chambres"
  }
]
```

## Troubleshooting

**403 Forbidden:**
- Cookies expirés → Ré-extraire avec Selenium
- Cookie `datadome` manquant → Vérifier `.cookies`
- IP blacklistée temporairement → Attendre 5-10 min

**0 annonces trouvées (status 200):**
- HTML structure changée → Analyser XPath selectors
- Script debug rapide:
```python
from lxml import html
doc = html.fromstring(open('response.html', 'rb').read())
len(doc.xpath("//div[@data-testid='sl.explore.card-container']"))
```

**Selenium crash:**
- Chrome/Chromium manquant → `apt install chromium-browser`
- Permissions → `chmod +x chromedriver`
- Headless fail → Retirer `--headless` des options Chrome

## Structure du code

### scrap.py - SeLogerScraper class

```python
__init__(cookies_file)          # Charge cookies, configure session
_load_cookies()                 # Parse JSON/text cookies → session
build_search_url(filters)       # Construit URL avec paramètres
search(filters, url, max_pages) # Visite homepage → scrape N pages
_parse_listings(html_content)   # XPath extraction → liste dicts
save_to_json(results, filename) # Dump JSON avec encoding UTF-8
```

**Pagination interne:**
- Boucle sur `max_pages` (défaut: 1)
- Ajoute `&LISTING-LISTpg=N` à l'URL
- Visite homepage (page 1 uniquement)
- Accumule résultats dans `all_results`
- Déduplique par URL avec `set()`
- Réindexe IDs de 1 à N
- Délai 3-5s entre pages

### enrich_annonces.py - AnnonceEnricher class

```python
__init__(cookies_file)                  # Configure session avec cookies
extract_details_from_page(url)          # Scrape page annonce complète
clean_surface(surface_str)              # Extrait float depuis "105 m²"
clean_location(location_str)            # Parse ville/quartier
enrich_annonces(annonces)               # Enrichit liste complète
save_to_json(results, filename)         # Sauvegarde JSON enrichi
```

**Extraction des détails:**
- JSON-LD structured data (GPS, adresse)
- XPath sur éléments `data-*` (DPE, GES)
- Regex pour dates et surfaces
- Galerie d'images (dédupliquées)
- Délai 2-4s entre annonces

### extract_cookies_selenium.py - CookieExtractor class

```python
__init__()                      # Configure Chrome avec options anti-bot
navigate_to_seloger()           # Ouvre SeLoger dans Chrome
wait_for_user_interaction()     # Pause pour login manuel
extract_cookies()               # Récupère tous les cookies du driver
save_cookies_simple_format()    # Sauvegarde JSON simple
save_cookies_full_format()      # Sauvegarde JSON complet avec metadata
verify_cookies()                # Vérifie présence cookies critiques
```

## Paramètres modifiables

**Filtres de recherche (scrap.py ligne ~120):**
```python
default_filters = {
    'projects': '1',              # 1=Location, 2=Vente
    'types': '1,2',               # 1=Appart, 2=Maison, 4=Parking
    'places': '[{ci:690123},{ci:690244}]',  # Codes INSEE
    'price': 'NaN/1500',         # Min/Max
    'surface': '65/NaN',         # Min/Max m²
    'bedrooms': '3',             # Min chambres
}
```

**Délais anti-bot (scrap.py ligne ~58):**
```python
self._min_delay = 2.0  # secondes
self._max_delay = 4.0
```

**Codes INSEE villes (à ajouter dans `places`):**
- Lyon: 690123
- Tassin-la-Demi-Lune: 690244
- Villeurbanne: 690266
- Vénissieux: 690259

Format: `[{ci:690123},{ci:690244},{ci:690266}]`

## Notes techniques

**Protection DataDome:**
- Fingerprinting navigateur (Canvas, WebGL, fonts)
- Analyse comportementale (mouvements souris, timing)
- Challenge invisible (JavaScript, cookies)
- Contournement: cookies extraits d'un vrai navigateur

**Selenium options critiques:**
```python
--disable-blink-features=AutomationControlled
--disable-dev-shm-usage
--no-sandbox
user-agent=Mozilla/5.0...
```

**Limites:**
- Cookies < 1h de validité
- Rate limiting: ~1 requête/2-4s recommandé
- Pagination: ~27 annonces/page (testée jusqu'à 10 pages)
- Photos non téléchargées (URLs disponibles dans HTML)
- Limite SeLoger: ~5-10 pages max par recherche

## Visualisation Web

Un visualiseur web moderne est disponible dans le dossier `webview/`. Il permet de consulter les annonces récupérées avec une interface élégante et intuitive.

**Fonctionnalités:**
- 🔍 Recherche en temps réel (titre, localisation, prix)
- 🔄 Tri par prix ou surface (croissant/décroissant)
- 🖼️ Galerie d'images pour chaque annonce
- 📱 Design responsive (mobile & desktop)
- 🗺️ Affichage GPS, DPE, GES si disponibles
- 🏷️ Tags visuels pour les caractéristiques

**Lancement rapide:**
```bash
cd webview
python3 server.py
# Ouvrir http://localhost:8000 dans votre navigateur
```

**Mise à jour des données:**
```bash
# Après chaque scraping, copier les nouvelles annonces
cp annonces.json annonces_enriched.json webview/
```

Pour plus de détails, consultez `webview/README_WEBVIEW.md`.
