# 🏠 Visualiseur d'Annonces Immobilières

Un projet web simple et élégant pour visualiser les annonces immobilières scrapées.

## 📋 Fonctionnalités

- ✨ Interface moderne et responsive
- 🔍 Recherche en temps réel (titre, localisation, prix)
- 🔄 Tri par prix ou surface (croissant/décroissant)
- 🖼️ Affichage des images
- 📱 Compatible mobile et desktop
- 🎨 Design moderne avec animations fluides
- 🔗 Liens directs vers les annonces originales
- 📊 Visualisation des tags et caractéristiques
- 🗺️ Affichage des coordonnées GPS (si disponibles)
- ⚡ DPE et GES (si disponibles)

## 🚀 Démarrage rapide

### Méthode 1 : Serveur Python (Recommandé)

```bash
# Lancer le serveur
python3 server.py

# Ouvrir dans votre navigateur
# http://localhost:8000
```

### Méthode 2 : Ouvrir directement le fichier HTML

```bash
# Dans votre navigateur, ouvrir :
file:///home/tobesson/code/python/appart/index.html
```

⚠️ Note : Certains navigateurs peuvent bloquer le chargement des fichiers JSON locaux pour des raisons de sécurité. Dans ce cas, utilisez la méthode 1.

## 📁 Structure du projet

```
appart/
├── index.html          # Page principale
├── style.css           # Styles CSS
├── app.js             # Logique JavaScript
├── server.py          # Serveur web Python (optionnel)
├── annonces.json      # Données des annonces simples
├── annonces_enriched.json  # Données enrichies (avec images, tags, GPS, etc.)
└── README_WEBVIEW.md  # Cette documentation
```

## 🎯 Utilisation

1. **Choisir la source de données** : Utilisez le menu déroulant en haut pour basculer entre les annonces simples et enrichies

2. **Rechercher** : Tapez dans la barre de recherche pour filtrer par titre, localisation, prix, etc.

3. **Trier** : Utilisez le menu de tri pour organiser les annonces par prix ou surface

4. **Voir les détails** : Cliquez sur une carte pour voir tous les détails dans une fenêtre modale

5. **Accéder à l'annonce** : Cliquez sur "Voir l'annonce complète" pour ouvrir le lien original

## 🎨 Personnalisation

Les couleurs et styles peuvent être facilement modifiés dans `style.css` via les variables CSS :

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #3b82f6;
    --background: #f8fafc;
    /* ... */
}
```

## 🔧 Technologies utilisées

- **HTML5** : Structure de la page
- **CSS3** : Design moderne avec Grid et Flexbox
- **JavaScript ES6+** : Logique et interactions
- **Python 3** : Serveur web simple (optionnel)

## 📝 Notes

- Le projet est entièrement statique (pas de base de données)
- Les données sont chargées depuis les fichiers JSON
- Aucune dépendance externe (pas de framework)
- Compatible avec tous les navigateurs modernes

## 🐛 Dépannage

**Les images ne s'affichent pas ?**
- Vérifiez que les URLs des images sont accessibles
- Une image de remplacement s'affiche automatiquement si l'image est indisponible

**Les annonces ne se chargent pas ?**
- Utilisez le serveur Python (`python3 server.py`) au lieu d'ouvrir directement le HTML
- Vérifiez que les fichiers JSON sont valides

**Erreur CORS ?**
- Le serveur Python inclut automatiquement les headers CORS
- Sinon, utilisez un autre serveur web local

## 📄 Licence

Projet libre d'utilisation et de modification.

---

Créé avec ❤️ pour visualiser vos annonces immobilières
