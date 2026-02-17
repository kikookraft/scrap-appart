#!/usr/bin/env python3
"""
Script de test pour vérifier le scraper sans cookies
"""

from scrap import SeLogerScraper

def test_without_cookies():
    """Test basique sans cookies"""
    print("=== Test du scraper SeLoger ===\n")
    
    # Créer le scraper
    scraper = SeLogerScraper(cookies_file='non_existent.cookies')
    
    # Test de construction d'URL
    url = scraper.build_search_url({
        'locations': 'FR069123',
        'spaceMin': '30'
    })
    print(f"URL générée: {url}\n")
    
    # Test de recherche (attendu: erreur 403 sans cookies)
    print("Test de recherche (devrait échouer sans cookies):")
    results = scraper.search(url=url)
    
    if results:
        print(f"✅ {len(results)} annonces trouvées")
        scraper.save_to_json(results, 'test_results.json')
    else:
        print("\n⚠️  Comme prévu, pas d'annonces sans cookies valides")
        print("👉 Consultez COOKIES_HELP.md pour configurer vos cookies")

if __name__ == "__main__":
    test_without_cookies()
