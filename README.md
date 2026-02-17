# SeLoger Scraper

Scraper d'annonces immobilières SeLoger avec authentification par cookies et contournement anti-bot DataDome.

## Architecture

```
scrap.py                          # Scraper principal (requests + lxml)
extract_cookies_selenium.py       # Extracteur de cookies (Selenium + Chrome)
.cookies                          # Cookies au format JSON simple
annonces.json                     # Résultats de scraping
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
python3 scrap.py
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
python3 scrap.py --url "https://..."  # URL personnalisée
python3 scrap.py --output results.json
```

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
search(filters, url)            # Visite homepage → search → parse
_parse_listings(html_content)   # XPath extraction → liste dicts
save_to_json(results, filename) # Dump JSON avec encoding UTF-8
```

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
- Pagination non implémentée (1 page = ~27 annonces)
- Photos non téléchargées (URLs disponibles dans HTML)
