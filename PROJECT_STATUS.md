# 🏠 Projet SeLoger Scraper - État Actuel

## ✅ Fonctionnalités Implémentées

### 1. Système de Connexion avec Cookies
- ✅ Chargement des cookies depuis un fichier `.cookies`
- ✅ Support de plusieurs formats de cookies:
  - JSON simple (dictionnaire)
  - JSON complet (export navigateur)
  - Format texte (name=value; name2=value2)
- ✅ Gestion gracieuse si les cookies sont manquants

### 2. Système de Recherche
- ✅ Construction automatique d'URLs de recherche
- ✅ Filtres par défaut pour Lyon et Tassin-la-Demi-Lune
- ✅ Support des filtres personnalisables:
  - `distributionTypes` (Rent/Sale)
  - `estateTypes` (House/Apartment)
  - `locations` (codes de villes)
  - `spaceMin` (surface minimum)
  - Et plus...

### 3. Extraction des Annonces
- ✅ Parsing HTML avec lxml
- ✅ Extraction des informations:
  - URL de l'annonce
  - Titre
  - Prix
  - Localisation
  - ID unique
- ✅ Gestion des erreurs de parsing

### 4. Export JSON
- ✅ Sauvegarde dans un fichier JSON
- ✅ Format UTF-8 avec indentation
- ✅ Structure propre et lisible

### 5. CLI (Interface Ligne de Commande)
- ✅ Arguments en ligne de commande
- ✅ Options:
  - `--url` : URL personnalisée
  - `--cookies` : Fichier de cookies
  - `--output` : Fichier de sortie
  - `--surface-min` : Surface minimum
- ✅ Messages colorés et informatifs

## 📁 Structure du Projet

```
appart/
├── scrap.py              # Script principal
├── test_scraper.py       # Script de test
├── requirements.txt      # Dépendances Python
├── README.md            # Documentation principale
├── COOKIES_HELP.md      # Guide pour les cookies
├── PROJECT_STATUS.md    # Ce fichier
├── .cookies.example     # Exemple de fichier cookies
└── .gitignore          # Fichiers à ignorer
```

## 🚀 Utilisation Rapide

### Installation
```bash
pip3 install -r requirements.txt
```

### Configuration des cookies
1. Voir `COOKIES_HELP.md` pour récupérer vos cookies
2. Créer un fichier `.cookies` au format JSON
3. Exemple dans `.cookies.example`

### Lancement
```bash
# Recherche par défaut (Lyon + Tassin)
python3 scrap.py

# Avec URL personnalisée
python3 scrap.py --url "https://..."

# Avec filtres
python3 scrap.py --surface-min 30
```

## ⚠️ Limitations Actuelles

### Protection Anti-Bot
- SeLoger utilise DataDome pour la protection anti-bot
- **Sans cookies valides → Erreur 403**
- Les cookies doivent être récents et valides
- Le cookie `datadome` est crucial

### Cookies Requis
Pour que le scraper fonctionne, vous DEVEZ:
1. Visiter seloger.com dans un navigateur
2. Récupérer vos cookies (voir COOKIES_HELP.md)
3. Les placer dans `.cookies`

### Pagination
- ⚠️ Actuellement, seule la première page est scrapée
- TODO: Implémenter la pagination

### Informations Limitées
- ⚠️ Seules les infos de base sont extraites (titre, prix, lieu)
- TODO: Extraire plus de détails (surface, nombre de pièces, etc.)

## 🔮 Développements Futurs

### Phase 1: Amélioration de Base
- [ ] Pagination automatique
- [ ] Extraction d'informations supplémentaires:
  - Nombre de pièces
  - Surface exacte
  - Étage
  - DPE
  - Date de publication
  - Description complète
- [ ] Gestion du rate limiting

### Phase 2: Filtrage Avancé
- [ ] Interface pour définir des filtres complexes
- [ ] Sauvegarde de profils de recherche
- [ ] Filtres post-scraping (sur les résultats)
- [ ] Exclusion de mots-clés

### Phase 3: Fonctionnalités Avancées
- [ ] Détection de nouvelles annonces
- [ ] Notifications (email, Telegram, etc.)
- [ ] Comparaison de prix
- [ ] Export vers différents formats (CSV, Excel, etc.)
- [ ] Interface web simple
- [ ] Base de données pour historique

### Phase 4: Multi-Sites
- [ ] Support de LeBonCoin
- [ ] Support de PAP
- [ ] Support d'autres sites immobiliers
- [ ] Agrégation des résultats

## 🐛 Problèmes Connus

1. **Erreur 403 sans cookies**
   - Normal, c'est la protection anti-bot
   - Solution: Configurer les cookies

2. **Cookies expirés**
   - Les cookies ont une durée de vie limitée
   - Solution: Les renouveler régulièrement

3. **Structure HTML changeante**
   - SeLoger peut modifier sa structure HTML
   - Solution: Adapter les XPath au besoin

## 📝 Notes Techniques

### Technologies Utilisées
- **Python 3.10+**
- **requests**: Requêtes HTTP
- **lxml**: Parsing HTML/XML
- **argparse**: CLI
- **json**: Sérialisation

### Architecture
- Classe `SeLogerScraper` principale
- Séparation des responsabilités:
  - Chargement cookies
  - Construction URL
  - Requête HTTP
  - Parsing HTML
  - Export JSON

### Bonnes Pratiques
- Type hints pour la lisibilité
- Gestion d'erreurs robuste
- Messages utilisateur clairs
- Documentation inline
- Séparation config/code

## 🎯 Prochaines Étapes Recommandées

1. **Configurer vos cookies** (priorité 1)
   - Voir `COOKIES_HELP.md`
   - Tester avec `python3 scrap.py`

2. **Tester le scraper**
   - Lancer une recherche test
   - Vérifier le fichier `annonces.json`

3. **Personnaliser les filtres**
   - Modifier les filtres par défaut
   - Ajouter vos propres critères

4. **Développer les fonctionnalités manquantes**
   - Pagination
   - Plus d'infos extraites
   - Filtres avancés

## 📞 Support

Si vous rencontrez des problèmes:
1. Vérifiez que vos cookies sont valides
2. Consultez les fichiers HELP
3. Regardez les messages d'erreur détaillés
4. Testez avec `test_scraper.py`

---

**Statut du projet**: ✅ Base fonctionnelle
**Dernière mise à jour**: 17 février 2026
**Version**: 1.0.0
