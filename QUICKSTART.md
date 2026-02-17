# 🚀 Guide de Démarrage Rapide

## Installation en 3 étapes

### 1. Installer les dépendances
```bash
pip3 install -r requirements.txt
```

### 2. Configurer les cookies

**Option A: Vous avez déjà un fichier `.cookies`**
- Parfait ! Passez à l'étape 3

**Option B: Vous devez créer le fichier `.cookies`**
- Consultez `COOKIES_HELP.md` pour les instructions détaillées
- En résumé:
  1. Ouvrez Chrome/Firefox
  2. Allez sur https://www.seloger.com
  3. Ouvrez DevTools (F12)
  4. Application → Cookies → seloger.com
  5. Copiez les cookies dans `.cookies` (format JSON)

Exemple de `.cookies`:
```json
{
  "visitId": "1708185600000-123456789",
  "_ga": "GA1.2.987654321.1708185600",
  "datadome": "votre_token_datadome_ici"
}
```

### 3. Lancer le scraper

**Recherche simple (Lyon + Tassin):**
```bash
python3 scrap.py
```

**Avec URL personnalisée:**
```bash
python3 scrap.py --url "https://www.seloger.com/classified-search?..."
```

## 🎯 Exemples d'Utilisation

### Recherche pour Lyon avec surface min 30m²
```bash
python3 scrap.py --surface-min 30
```

### Avec un fichier de cookies spécifique
```bash
python3 scrap.py --cookies mes_cookies.json
```

### Sauvegarder dans un fichier spécifique
```bash
python3 scrap.py --output resultats_lyon.json
```

### Tout combiné
```bash
python3 scrap.py \
  --cookies .cookies \
  --output annonces_lyon.json \
  --surface-min 35
```

## 📊 Résultats

Les annonces sont sauvegardées dans `annonces.json` par défaut:

```json
[
  {
    "id": 1,
    "url": "https://www.seloger.com/annonces/...",
    "title": "Appartement 2 pièces 45 m²",
    "price": "850 € CC",
    "location": "Lyon 6ème"
  },
  ...
]
```

## ⚠️ Problèmes Courants

### Erreur 403 (Accès Refusé)
**Cause**: Cookies manquants ou invalides
**Solution**: 
1. Vérifiez que `.cookies` existe
2. Assurez-vous que les cookies sont récents
3. Rafraîchissez vos cookies depuis le navigateur

### Aucune annonce trouvée
**Cause**: Plusieurs possibilités
- Protection anti-bot (cookies invalides)
- Aucune annonce ne correspond aux critères
- Structure HTML changée

**Solution**:
1. Vérifiez les cookies
2. Testez avec une recherche plus large
3. Regardez les messages de debug

### Module not found: lxml
**Solution**:
```bash
pip3 install -r requirements.txt
```

## 🔧 Customisation

### Modifier les filtres par défaut

Éditez `scrap.py`, ligne ~100:
```python
default_filters = {
    'distributionTypes': 'Rent',  # ou 'Sale' pour vente
    'estateTypes': 'House,Apartment',
    'locations': 'FR069123,FR069244',  # Codes villes
    'spaceMin': '28',
}
```

### Codes de localisation utiles
- Lyon: `FR069123`
- Tassin-la-Demi-Lune: `FR069244`
- Villeurbanne: `FR069266`
- Caluire-et-Cuire: `FR069034`

### Ajouter d'autres filtres
Consultez les URLs de SeLoger pour voir les paramètres disponibles:
- `priceMin`, `priceMax`: Prix
- `roomsMin`, `roomsMax`: Nombre de pièces
- `bedroomsMin`: Chambres
- etc.

## 📚 Documentation

- **README.md**: Documentation complète
- **COOKIES_HELP.md**: Guide détaillé sur les cookies
- **PROJECT_STATUS.md**: État du projet et roadmap
- **Ce fichier**: Guide de démarrage rapide

## 🧪 Tester Sans Cookies

Pour tester la structure du code sans cookies:
```bash
python3 test_scraper.py
```

Vous verrez une erreur 403, c'est normal !

## 📞 Aide

Si ça ne fonctionne pas:
1. ✅ Les dépendances sont installées ? (`pip3 install -r requirements.txt`)
2. ✅ Le fichier `.cookies` existe et contient des données ?
3. ✅ Les cookies sont récents (< 1 jour) ?
4. ✅ Vous avez testé l'URL dans un navigateur d'abord ?

---

**Bon scraping ! 🦀**
