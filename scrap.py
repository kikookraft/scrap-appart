import requests
from lxml import html
import argparse
import json
import os
import time
import random
from typing import Dict, List, Optional

def get_realistic_headers():
    """
    Génère des headers réalistes pour éviter la détection
    """
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',  # Changé pour simuler navigation directe
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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
        
        # Configurer la session pour ressembler à un vrai navigateur
        self._s.headers.update(get_realistic_headers())
        
        # Charger les cookies
        self._load_cookies()
        
        # Ajouter un délai aléatoire entre les requêtes
        self._last_request_time = 0
        self._min_delay = 2  # Minimum 2 secondes entre requêtes
        
    def _wait_before_request(self):
        """Attend un délai aléatoire avant la requête pour éviter la détection"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay:
            wait_time = self._min_delay - elapsed + random.uniform(0.5, 2.0)
            print(f"⏳ Attente de {wait_time:.1f}s pour éviter la détection...")
            time.sleep(wait_time)
        self._last_request_time = time.time()
        
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
        base_url = "https://www.seloger.com/list.htm"
        
        # Filtres par défaut pour Lyon et Tassin-la-Demi-Lune
        # 1500€ max, 65m² min, 3 chambres min
        default_filters = {
            'projects': '1',              # 1 = Location, 2 = Vente
            'types': '1,2',               # 1 = Appartement, 2 = Maison
            'places': '[{ci:690123},{ci:690244}]',  # Lyon et Tassin
            'price': 'NaN/1500',         # Min/Max prix (NaN = pas de min)
            'surface': '65/NaN',         # Min/Max surface (NaN = pas de max)
            'bedrooms': '3',             # Nombre de chambres minimum
            'enterprise': '0',           # Pas d'annonces professionnelles
            'qsVersion': '1.0',
            'm': 'search_refine-redirection-search_results',
        }
        
        # Fusionner avec les filtres fournis
        if filters:
            default_filters.update(filters)
        
        # Construire l'URL avec les paramètres
        # URL-encoder les paramètres spéciaux
        import urllib.parse
        params_list = []
        for k, v in default_filters.items():
            if k == 'places':
                # Encoder correctement le paramètre places
                encoded = urllib.parse.quote(str(v), safe='')
                params_list.append(f"{k}={encoded}")
            else:
                params_list.append(f"{k}={v}")
        
        params = '&'.join(params_list)
        return f"{base_url}?{params}"

    def search(
        self,
        filters: Optional[Dict] = None,
        url: Optional[str] = None,
        max_pages: int = 1,
        exclude_colocation: bool = True
    ) -> List[Dict]:
        """
        Effectue une recherche et retourne les annonces
        
        Args:
            filters: Filtres de recherche (optionnel)
            url: URL directe (optionnel, prioritaire sur filters)
            max_pages: Nombre maximum de pages à scraper (défaut: 1)
            exclude_colocation: Filtrer les colocations (défaut: True)
            
        Returns:
            Liste de dictionnaires représentant les annonces
        """
        all_results = []
        
        for page_num in range(1, max_pages + 1):
            print(f"\n{'='*60}")
            print(f"📄 PAGE {page_num}/{max_pages}")
            print('='*60)
            
            # Construire l'URL avec pagination
            if url:
                # URL fournie: ajouter paramètre de page
                base_url = url
                separator = '&' if '?' in base_url else '?'
                if page_num > 1:
                    search_url = f"{base_url}{separator}LISTING-LISTpg={page_num}"
                else:
                    search_url = base_url
            else:
                # Construire avec filtres
                base_filters = filters.copy() if filters else {}
                if page_num > 1:
                    base_filters['LISTING-LISTpg'] = str(page_num)
                search_url = self.build_search_url(base_filters)
            
            print(f"🔍 Recherche sur: {search_url}")
            
            # Attendre avant la requête pour éviter la détection
            self._wait_before_request()
            
            # Étape 1: Visiter la page d'accueil (première page seulement)
            if page_num == 1:
                print("🏠 Visite de la page d'accueil...")
                try:
                    home_headers = get_realistic_headers()
                    home_response = self._s.get(
                        'https://www.seloger.com/',
                        headers=home_headers,
                        timeout=30,
                        allow_redirects=True
                    )
                    if home_response.status_code == 200:
                        print("✅ Page d'accueil chargée")
                    else:
                        status = home_response.status_code
                        print(f"⚠️  Page d'accueil: status {status}")
                    
                    # Petit délai pour simuler la lecture
                    time.sleep(random.uniform(1.5, 3.0))
                except Exception as e:
                    print(f"⚠️  Erreur page d'accueil: {e}")
            
            # Étape 2: Effectuer la vraie requête
            print("📋 Chargement des résultats de recherche...")
            self._wait_before_request()
            
            try:
                # Headers mis à jour avec le referer
                search_headers = get_realistic_headers()
                search_headers['Referer'] = 'https://www.seloger.com/'
                search_headers['Sec-Fetch-Site'] = 'same-origin'
                
                response = self._s.get(
                    search_url,
                    headers=search_headers,
                    timeout=30,
                    allow_redirects=True
                )
            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur de connexion: {e}")
                break
            
            if response.status_code == 403:
                print("❌ Accès refusé (403) - Protection anti-bot")
                print("💡 Suggestions avancées:")
                print("   1. Cookies expirés (< 1 jour)")
                print("   2. Ouvrez SeLoger dans Chrome et:")
                print("      - Faites la même recherche manuellement")
                print("      - Exportez les cookies JUSTE APRÈS")
                print("      - Replacez-les dans .cookies")
                print("   3. Le cookie 'datadome' change à chaque session")
                print(f"   4. Cookies: {len(self._s.cookies)} chargés")
                print("\n🔧 Debug: Cookies présents:")
                for cookie in self._s.cookies:
                    print(f"      - {cookie.name}")
                break
            
            if response.status_code != 200:
                print(f"❌ Erreur HTTP {response.status_code}")
                break
            
            print(f"✅ Réponse reçue (status: {response.status_code})")
            
            # Parser les résultats
            page_results = self._parse_listings(response.content)
            
            if not page_results:
                print(f"⚠️  Aucune annonce sur la page {page_num}, arrêt")
                break
                
            all_results.extend(page_results)
            print(f"📊 Total cumulé: {len(all_results)} annonces")
            
            # Ne pas attendre après la dernière page
            if page_num < max_pages:
                delay = random.uniform(3.0, 5.0)
                print(f"⏳ Pause de {delay:.1f}s avant page suivante...")
                time.sleep(delay)
        
        # Dédupliquer par URL et réindexer
        seen_urls = set()
        unique_results = []
        for annonce in all_results:
            url = annonce.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(annonce)
        
        if len(unique_results) < len(all_results):
            duplicates = len(all_results) - len(unique_results)
            print(f"🔄 {duplicates} doublons supprimés")
        
        # Filtrer les colocations si demandé
        if exclude_colocation:
            colocation_keywords = [
                'coloc', 'colocation', 'chambre disponible', 'chambre meublée',
                'espace commun', 'colocataire'
            ]
            
            filtered_results = []
            excluded_count = 0
            
            for annonce in unique_results:
                # Vérifier titre et description
                title = annonce.get('title', '').lower()
                location = annonce.get('location', '').lower()
                
                is_colocation = any(
                    keyword in title or keyword in location
                    for keyword in colocation_keywords
                )
                
                if not is_colocation:
                    filtered_results.append(annonce)
                else:
                    excluded_count += 1
            
            if excluded_count > 0:
                print(f"� {excluded_count} colocations exclues")
            
            unique_results = filtered_results
        
        # Réindexer avec des IDs uniques
        for i, annonce in enumerate(unique_results, 1):
            annonce['id'] = i
        
        return unique_results

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
            
            # Nouveau sélecteur: chercher les conteneurs d'annonces
            # (mis à jour suite à l'analyse de la structure HTML)
            listings = doc.xpath(
                "//div[@data-testid='sl.explore.card-container']"
            )
            
            print(f"📋 {len(listings)} annonces trouvées")
            
            for i, listing in enumerate(listings, 1):
                try:
                    # Extraire l'URL
                    url_path_list = listing.xpath(
                        ".//a[@data-testid='sl.explore.coveringLink']/@href"
                    )
                    url_path = url_path_list[0] if url_path_list else ""
                    url = f"https://www.seloger.com{url_path}" if url_path else ""
                    
                    # Extraire le prix
                    price_texts = listing.xpath(
                        ".//div[@data-testid='sl.explore-card-price']//text()"
                    )
                    price_texts = [t.strip() for t in price_texts if t.strip()]
                    price = price_texts[0] if price_texts else ""
                    
                    # Extraire tous les textes pour obtenir infos
                    all_texts = listing.xpath(".//text()")
                    all_texts = [t.strip() for t in all_texts
                                 if t.strip() and len(t.strip()) > 2]
                    
                    # Le titre est généralement après le prix
                    title = ""
                    location = ""
                    surface = ""
                    bedrooms = ""
                    
                    for idx, text in enumerate(all_texts):
                        # Le titre contient souvent "Appartement" ou "Maison"
                        if "Appartement" in text or "Maison" in text:
                            title = text
                        # La localisation contient souvent un code postal
                        if "(" in text and ")" in text and any(
                            c.isdigit() for c in text
                        ):
                            location = text
                        # Surface
                        if "m²" in text:
                            surface = text
                        # Chambres
                        if "chambre" in text:
                            bedrooms = text
                    
                    # Créer l'objet annonce
                    annonce = {
                        'id': i,
                        'url': url,
                        'title': title,
                        'price': price,
                        'location': location,
                        'surface': surface,
                        'bedrooms': bedrooms,
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
    argparser.add_argument(
        '--max-pages',
        type=int,
        default=10,
        help='Nombre maximum de pages à scraper (défaut: 10)'
    )
    argparser.add_argument(
        '--include-colocation',
        action='store_true',
        help='Inclure les colocations (par défaut: exclues)'
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
    
    # Déterminer si on exclut les colocations
    exclude_coloc = not args.include_colocation
    
    # Effectuer la recherche
    if args.url:
        results = scraper.search(
            url=args.url,
            max_pages=args.max_pages,
            exclude_colocation=exclude_coloc
        )
    else:
        # URL par défaut pour Lyon et Tassin-la-Demi-Lune
        print("🏙️  Recherche pour Lyon et Tassin-la-Demi-Lune")
        if exclude_coloc:
            print("🚫 Exclusion des colocations activée")
        results = scraper.search(
            filters=filters,
            max_pages=args.max_pages,
            exclude_colocation=exclude_coloc
        )
    
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
