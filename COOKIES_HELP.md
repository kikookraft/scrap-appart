# Guide pour récupérer vos cookies SeLoger

## Option 1: Récupération manuelle via DevTools

1. Ouvrez Chrome ou Firefox
2. Allez sur https://www.seloger.com
3. Ouvrez les DevTools (F12)
4. Allez dans l'onglet "Application" (Chrome) ou "Stockage" (Firefox)
5. Sélectionnez "Cookies" > "https://www.seloger.com"
6. Copiez les cookies importants dans un fichier `.cookies` au format JSON

### Format simple (recommandé):

```json
{
  "visitId": "VOTRE_VISIT_ID",
  "_ga": "VOTRE_GA",
  "datadome": "VOTRE_DATADOME_TOKEN"
}
```

## Option 2: Export avec extension navigateur

### Avec EditThisCookie (Chrome)

1. Installez l'extension "EditThisCookie"
2. Visitez seloger.com
3. Cliquez sur l'icône de l'extension
4. Cliquez sur "Export" (icône floppy disk)
5. Collez le contenu dans `.cookies`

### Avec Cookie-Editor (Firefox/Chrome)

1. Installez l'extension "Cookie-Editor"
2. Visitez seloger.com
3. Cliquez sur l'icône de l'extension
4. Cliquez sur "Export" > "JSON"
5. Collez dans `.cookies`

## Option 3: Capture des cookies depuis les requêtes réseau

1. Ouvrez les DevTools (F12)
2. Allez dans l'onglet "Network" (Réseau)
3. Visitez une page de recherche sur seloger.com
4. Sélectionnez une requête vers seloger.com
5. Dans les headers, cherchez "Cookie:"
6. Copiez toute la chaîne de cookies
7. Créez `.cookies` avec le contenu:

```
nom1=valeur1; nom2=valeur2; nom3=valeur3
```

## Cookies importants à récupérer

Les cookies essentiels pour SeLoger sont:
- `datadome` - Protection anti-bot
- `visitId` - Identifiant de session
- `_ga`, `_gid` - Google Analytics
- Cookies de consentement (RGPD)

## Exemple de fichier .cookies fonctionnel

```json
{
  "visitId": "1708185600000-123456789",
  "_ga": "GA1.2.987654321.1708185600",
  "_gid": "GA1.2.123456789.1708185600",
  "datadome": "token_datadome_très_long_ici",
  "euconsent-v2": "votre_consent_string"
}
```

## Test

Une fois le fichier `.cookies` créé, testez avec:

```bash
python3 scrap.py
```

Si vous voyez "✅ X cookies chargés", c'est bon !
