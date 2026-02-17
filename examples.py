#!/usr/bin/env python3
"""
Exemple d'utilisation programmatique du scraper SeLoger
"""

from scrap import SeLogerScraper

# Exemple 1: Recherche simple
def exemple_simple():
    print("=== Exemple 1: Recherche Simple ===\n")
    scraper = SeLogerScraper(cookies_file='.cookies')
    results = scraper.search()
    print(f"Trouvé {len(results)} annonces\n")
    return results


# Exemple 2: Avec filtres personnalisés
def exemple_avec_filtres():
    print("=== Exemple 2: Avec Filtres ===\n")
    scraper = SeLogerScraper(cookies_file='.cookies')
    
    filtres = {
        'locations': 'FR069123',  # Lyon uniquement
        'spaceMin': '40',          # Minimum 40m²
        'priceMax': '1000',        # Maximum 1000€
        'roomsMin': '2',           # Au moins 2 pièces
    }
    
    results = scraper.search(filters=filtres)
    print(f"Trouvé {len(results)} annonces\n")
    return results


# Exemple 3: Construction d'URL personnalisée
def exemple_url_personnalisee():
    print("=== Exemple 3: URL Personnalisée ===\n")
    scraper = SeLogerScraper(cookies_file='.cookies')
    
    url = scraper.build_search_url({
        'distributionTypes': 'Sale',  # Vente au lieu de location
        'estateTypes': 'Apartment',   # Seulement appartements
        'locations': 'FR069123',
        'spaceMin': '50',
        'priceMax': '200000',
    })
    
    print(f"URL: {url}\n")
    results = scraper.search(url=url)
    print(f"Trouvé {len(results)} annonces\n")
    return results


# Exemple 4: Traitement des résultats
def exemple_traitement():
    print("=== Exemple 4: Traitement des Résultats ===\n")
    scraper = SeLogerScraper(cookies_file='.cookies')
    results = scraper.search()
    
    if not results:
        print("Aucune annonce trouvée")
        return
    
    # Filtrer par prix
    print("Annonces à moins de 900€:")
    for annonce in results:
        price_str = annonce.get('price', '')
        # Extraire le nombre (simplifié)
        try:
            price = int(''.join(filter(str.isdigit, price_str)))
            if price < 900:
                print(f"  - {annonce['title']}: {annonce['price']}")
        except:
            pass
    
    # Statistiques
    print(f"\nStatistiques:")
    print(f"  Total: {len(results)} annonces")
    print(f"  Localisations uniques: {len(set(a['location'] for a in results))}")
    
    return results


# Exemple 5: Sauvegarde multiple formats
def exemple_sauvegarde():
    print("=== Exemple 5: Sauvegardes Multiples ===\n")
    scraper = SeLogerScraper(cookies_file='.cookies')
    results = scraper.search()
    
    if not results:
        print("Aucune annonce à sauvegarder")
        return
    
    # JSON complet
    scraper.save_to_json(results, 'annonces_complet.json')
    
    # JSON filtré (que les URLs)
    import json
    urls_only = [{'url': a['url'], 'title': a['title']} for a in results]
    with open('annonces_urls.json', 'w', encoding='utf-8') as f:
        json.dump(urls_only, f, ensure_ascii=False, indent=2)
    print("💾 Sauvegardé dans annonces_urls.json")
    
    # CSV simple
    import csv
    with open('annonces.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'price', 'location', 'url'])
        writer.writeheader()
        writer.writerows(results)
    print("💾 Sauvegardé dans annonces.csv")


# Menu principal
if __name__ == "__main__":
    import sys
    
    exemples = {
        '1': ('Recherche simple', exemple_simple),
        '2': ('Avec filtres', exemple_avec_filtres),
        '3': ('URL personnalisée', exemple_url_personnalisee),
        '4': ('Traitement des résultats', exemple_traitement),
        '5': ('Sauvegardes multiples', exemple_sauvegarde),
    }
    
    print("""
╔══════════════════════════════════════════════════════════╗
║              Exemples d'Utilisation du Scraper           ║
╚══════════════════════════════════════════════════════════╝

Choisissez un exemple:
""")
    
    for key, (desc, _) in exemples.items():
        print(f"  {key}. {desc}")
    
    print("\n  0. Tous les exemples")
    print("  q. Quitter")
    
    choix = input("\nVotre choix: ").strip()
    
    if choix == 'q':
        print("Au revoir! 🦀")
        sys.exit(0)
    
    if choix == '0':
        for desc, func in exemples.values():
            try:
                func()
            except Exception as e:
                print(f"❌ Erreur: {e}\n")
    elif choix in exemples:
        desc, func = exemples[choix]
        try:
            func()
        except Exception as e:
            print(f"❌ Erreur: {e}")
    else:
        print("❌ Choix invalide")
    
    print("\n✅ Terminé!")
