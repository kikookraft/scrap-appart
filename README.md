# SeLoger Scraper 🏠

Scraper d'annonces immobilières pour SeLoger avec support de filtres et authentification par cookies.

## Installation

```bash
pip install requests lxml
```

## Configuration des cookies

Pour utiliser le scraper avec authentification, vous devez créer un fichier `.cookies` contenant vos cookies de session SeLoger.

### Méthode 1: Format JSON simple (recommandé)

Créez un fichier `.cookies` avec le format JSON suivant:

```json
{
  "visitId": "1657611082733-168489653",
  "_gcl_au": "1.1.1398385248.1657611083",
  "datadome": "votre_token_datadome",
  "_ga": "GA1.2.418942909.1657611083"
}
```

### Méthode 2: Format JSON complet (export navigateur)

Vous pouvez aussi exporter vos cookies depuis le navigateur (avec une extension comme "EditThisCookie") et les coller dans `.cookies`:

```json
[
  {
    "name": "visitId",
    "value": "1657611082733-168489653",
    "domain": ".seloger.com",
    "path": "/"
  },
  {
    "name": "_ga",
    "value": "GA1.2.418942909.1657611083",
    "domain": ".seloger.com",
    "path": "/"
  }
]
```

### Comment récupérer vos cookies ?

1. **Via les DevTools du navigateur:**
   - Ouvrez Chrome/Firefox DevTools (F12)
   - Allez sur seloger.com et connectez-vous
   - Onglet "Application" > "Cookies" > "https://www.seloger.com"
   - Copiez les cookies importants (visitId, datadome, _ga, etc.)

2. **Via une extension:**
   - Installez "EditThisCookie" ou "Cookie-Editor"
   - Visitez seloger.com
   - Exportez les cookies au format JSON

## Utilisation

### Recherche basique (Lyon et Tassin-la-Demi-Lune)

```bash
python scrap.py
```

### Avec une URL personnalisée

```bash
python scrap.py --url "https://www.seloger.com/classified-search?distributionTypes=Rent&estateTypes=House,Apartment&locations=FR069123&spaceMin=28"
```

### Avec des filtres

```bash
python scrap.py --surface-min 35
```

### Spécifier un fichier de cookies différent

```bash
python scrap.py --cookies mes_cookies.json
```

### Spécifier un fichier de sortie

```bash
python scrap.py --output resultats.json
```

## Options disponibles

- `-u, --url`: URL de recherche SeLoger à scraper
- `-c, --cookies`: Fichier de cookies (défaut: `.cookies`)
- `-o, --output`: Fichier JSON de sortie (défaut: `annonces.json`)
- `--surface-min`: Surface minimum en m²

## Filtres de recherche

Le scraper supporte les filtres suivants (via la méthode `build_search_url`):

- `distributionTypes`: Type de transaction (Rent, Sale)
- `estateTypes`: Type de bien (House, Apartment, etc.)
- `locations`: Codes de localisation (FR069123 pour Lyon, FR069244 pour Tassin)
- `spaceMin`: Surface minimum en m²
- `priceMin`, `priceMax`: Fourchette de prix
- `roomsMin`, `roomsMax`: Nombre de pièces

## Codes de localisation

Quelques codes utiles pour la région lyonnaise:

- **Lyon**: FR069123
- **Tassin-la-Demi-Lune**: FR069244
- **Villeurbanne**: FR069266
- **Caluire-et-Cuire**: FR069034
- **Écully**: FR069081

Vous pouvez trouver d'autres codes en inspectant les URLs de recherche sur SeLoger.

## Exemple de résultat

Le fichier JSON généré contient:

```json
[
  {
    "id": 1,
    "url": "https://www.seloger.com/annonces/...",
    "title": "Appartement 2 pièces 45 m²",
    "price": "850 € CC",
    "location": "Lyon 6ème"
  },
  {
    "id": 2,
    "url": "https://www.seloger.com/annonces/...",
    "title": "Maison 4 pièces 80 m²",
    "price": "1 200 € CC",
    "location": "Tassin-la-Demi-Lune"
  }
]
```

## Développement futur

Le système de filtrage sera amélioré pour permettre:
- Filtres plus avancés (équipements, étage, DPE, etc.)
- Recherche multi-critères complexe
- Sauvegarde de profils de recherche
- Notifications pour nouvelles annonces
- Export dans d'autres formats (CSV, Excel, etc.)

## Notes

- Le scraper respecte les données publiques de SeLoger
- L'utilisation de cookies permet d'accéder aux fonctionnalités nécessitant une session
- Veillez à ne pas surcharger les serveurs avec trop de requêtes
