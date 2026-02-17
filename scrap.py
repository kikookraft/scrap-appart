import requests
from lxml import html
import argparse
import json
import os
from pathlib import Path
from http.cookiejar import MozillaCookieJar
from typing import Dict, List, Optional

# Headers de base (les cookies seront chargés séparément)
HEADERS = {
    'authority': 'www.seloger.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'referer': 'https://www.seloger.com/',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}


class SeLogerScraper:
    """Scraper pour les annonces immobilières SeLoger"""

    def __init__(self, cookies_file: str = '.cookies'):
        """
        Initialise le scraper avec les cookies
        
        Args:
            cookies_file: Chemin vers le fichier de cookies
        """
        self._s = requests.Session()
        self.cookies_file = cookies_file
        self._load_cookies()
        
    def _load_cookies(self):
        """Charge les cookies depuis le fichier"""
        if not os.path.exists(self.cookies_file):
            print(f"⚠️  Fichier de cookies '{self.cookies_file}' non trouvé")
            print("Le scraper continuera sans authentification")
            return
        
        try:
            # Essayer de charger comme fichier JSON simple
            with open(self.cookies_file, 'r') as f:
                cookies_data = json.load(f)
                
            # Si c'est un dictionnaire simple
            if isinstance(cookies_data, dict):
                for name, value in cookies_data.items():
                    self._s.cookies.set(name, value, domain='.seloger.com')
            # Si c'est un tableau de cookies (format export navigateur)
            elif isinstance(cookies_data, list):
                for cookie in cookies_data:
                    self._s.cookies.set(
                        cookie.get('name'),
                        cookie.get('value'),
                        domain=cookie.get('domain', '.seloger.com'),
                        path=cookie.get('path', '/')
                    )
            
            print(f"✅ {len(self._s.cookies)} cookies chargés depuis {self.cookies_file}")
            
        except json.JSONDecodeError:
            # Essayer de charger comme fichier texte avec une ligne par cookie
            try:
                with open(self.cookies_file, 'r') as f:
                    cookie_string = f.read().strip()
                    
                # Parser une chaîne de cookies (format: name=value; name2=value2)
                for cookie_pair in cookie_string.split(';'):
                    if '=' in cookie_pair:
                        name, value = cookie_pair.strip().split('=', 1)
                        self._s.cookies.set(name, value, domain='.seloger.com')
                        
                print(f"✅ Cookies chargés depuis {self.cookies_file}")
                
            except Exception as e:
                print(f"❌ Erreur lors du chargement des cookies: {e}")

    def build_search_url(self, filters: Optional[Dict] = None) -> str:
        """
        Construit l'URL de recherche avec les filtres
        
        Args:
            filters: Dictionnaire de filtres (locations, distributionTypes, etc.)
            
        Returns:
            URL de recherche complète
        """
        base_url = "https://www.seloger.com/classified-search"
        
        # Filtres par défaut pour Lyon et Tassin-la-Demi-Lune
        default_filters = {
            'distributionTypes': 'Rent',  # Location
            'estateTypes': 'House,Apartment',  # Maison et Appartement
            'locations': 'FR069123,FR069244',  # Lyon et Tassin-la-Demi-Lune
            'spaceMin': '28',  # Surface minimum
        }
        
        # Fusionner avec les filtres fournis
        if filters:
            default_filters.update(filters)
        
        # Construire l'URL avec les paramètres
        params = '&'.join([f"{k}={v}" for k, v in default_filters.items()])
        return f"{base_url}?{params}&m=homepage_relaunch_my_last_search_classified_search_result"

    def search(self, filters: Optional[Dict] = None, url: Optional[str] = None) -> List[Dict]:
        """
        Effectue une recherche et retourne les annonces
        
        Args:
            filters: Filtres de recherche (optionnel)
            url: URL directe (optionnel, prioritaire sur filters)
            
        Returns:
            Liste de dictionnaires représentant les annonces
        """
        # Utiliser l'URL fournie ou construire avec les filtres
        search_url = url if url else self.build_search_url(filters)
        
        print(f"🔍 Recherche sur: {search_url}")
        
        # Effectuer la requête
        try:
            response = self._s.get(search_url, headers=HEADERS, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return []
        
        if response.status_code == 403:
            print(f"❌ Accès refusé (403) - Protection anti-bot détectée")
            print("💡 Suggestions:")
            print("   1. Vérifiez que vos cookies sont valides et à jour")
            print("   2. Utilisez un navigateur pour visiter le site d'abord")
            print("   3. Le cookie 'datadome' est particulièrement important")
            print(f"   4. Cookies actuels: {len(self._s.cookies)} chargés")
            return []
        
        if response.status_code != 200:
            print(f"❌ Erreur HTTP {response.status_code}")
            return []
        
        print(f"✅ Réponse reçue (status: {response.status_code})")
        
        # Parser les résultats
        return self._parse_listings(response.content)

    def _parse_listings(self, html_content: bytes) -> List[Dict]:
        """
        Parse le HTML et extrait les annonces
        
        Args:
            html_content: Contenu HTML de la page
            
        Returns:
            Liste des annonces trouvées
        """
        results = []
        
        try:
            doc = html.fromstring(html_content)
            listings = doc.xpath("//div[@data-test='sl.card-container']")
            
            print(f"📋 {len(listings)} annonces trouvées")
            
            for i, listing in enumerate(listings, 1):
                try:
                    # Extraire les informations
                    url_path = "".join(
                        listing.xpath(
                            ".//div[contains(@class, 'Card__ContentZone')]"
                            "//a[contains(@name, 'classified-link')]/@href"
                        )
                    )
                    url = f"https://www.seloger.com{url_path}" if url_path else ""
                    
                    price = "".join(
                        listing.xpath(".//div[@data-test='sl.price-label']/text()")
                    ).strip()
                    
                    title = "".join(
                        listing.xpath(".//div[@data-test='sl.title']/text()")
                    ).strip()
                    
                    # Extraire des infos supplémentaires si disponibles
                    location = "".join(
                        listing.xpath(".//div[@data-test='sl.localisation']/text()")
                    ).strip()
                    
                    # Créer l'objet annonce
                    annonce = {
                        'id': i,
                        'url': url,
                        'title': title,
                        'price': price,
                        'location': location,
                    }
                    
                    results.append(annonce)
                    print(f"  {i}. {title} - {price} - {location}")
                    
                except Exception as e:
                    print(f"⚠️  Erreur lors du parsing de l'annonce {i}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing: {e}")
            return []

    def save_to_json(self, results: List[Dict], filename: str = 'annonces.json'):
        """
        Sauvegarde les résultats dans un fichier JSON
        
        Args:
            results: Liste des annonces
            filename: Nom du fichier de sortie
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"💾 {len(results)} annonces sauvegardées dans {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")

    def iter_listings(self, u):
        """Méthode legacy pour compatibilité"""
        response = self._s.get(u, headers=HEADERS)
        if response.status_code != 200:
            print(f'Erreur status code {response.status_code}')
            return []
        
        print(f'status code {response.status_code}')
        return self._parse_listings(response.content)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description='Scraper d\'annonces immobilières SeLoger'
    )
    argparser.add_argument(
        '--url', '-u',
        type=str,
        required=False,
        help='URL de recherche à scraper'
    )
    argparser.add_argument(
        '--cookies', '-c',
        type=str,
        default='.cookies',
        help='Fichier de cookies (défaut: .cookies)'
    )
    argparser.add_argument(
        '--output', '-o',
        type=str,
        default='annonces.json',
        help='Fichier de sortie JSON (défaut: annonces.json)'
    )
    argparser.add_argument(
        '--surface-min',
        type=int,
        help='Surface minimum en m²'
    )
    
    args = argparser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════╗
║         SeLoger Scraper - Annonces Immobilières          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Créer le scraper avec les cookies
    scraper = SeLogerScraper(cookies_file=args.cookies)
    
    # Préparer les filtres
    filters = {}
    if args.surface_min:
        filters['spaceMin'] = str(args.surface_min)
    
    # Effectuer la recherche
    if args.url:
        results = scraper.search(url=args.url)
    else:
        # URL par défaut pour Lyon et Tassin-la-Demi-Lune
        print("🏙️  Recherche pour Lyon et Tassin-la-Demi-Lune")
        results = scraper.search(filters=filters)
    
    # Sauvegarder les résultats
    if results:
        scraper.save_to_json(results, args.output)
        print(f"\n✅ Scraping terminé avec succès!")
        print(f"📊 {len(results)} annonces récupérées")
    else:
        print("\n⚠️  Aucune annonce trouvée")
    
    print("""
    
    🦀 lobstr 🦀
    """)
