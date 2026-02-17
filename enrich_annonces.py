#!/usr/bin/env python3
"""
Script d'enrichissement des annonces SeLoger
Récupère les détails complets de chaque annonce et ajoute:
- Localisation GPS (latitude, longitude, ville, quartier)
- Performance énergétique (DPE, GES)
- Liste des URLs d'images
- Surface et localisation nettoyées
- Date de récupération
- Date de publication de l'annonce
"""

import requests
from lxml import html
import argparse
import json
import os
import time
import random
import re
from typing import Dict, List, Optional
from datetime import datetime


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
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }


class AnnonceEnricher:
    """Enrichit les annonces avec des informations détaillées"""

    def __init__(self, cookies_file: str = '.cookies'):
        """
        Initialise l'enrichisseur avec les cookies
        
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
            time.sleep(wait_time)
        self._last_request_time = time.time()
        
    def _load_cookies(self):
        """Charge les cookies depuis le fichier"""
        if not os.path.exists(self.cookies_file):
            print(f"⚠️  Fichier de cookies '{self.cookies_file}' non trouvé")
            print("L'enrichisseur continuera sans authentification")
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

    def clean_surface(self, surface_str: str) -> Optional[float]:
        """
        Nettoie et extrait la surface en m²
        
        Args:
            surface_str: Chaîne contenant la surface
            
        Returns:
            Surface en float ou None
        """
        if not surface_str:
            return None
            
        # Chercher un nombre suivi de m²
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*m²', surface_str)
        if match:
            surface = match.group(1).replace(',', '.')
            try:
                return float(surface)
            except ValueError:
                return None
        return None

    def clean_location(self, location_str: str) -> Dict[str, Optional[str]]:
        """
        Nettoie et extrait ville et quartier de la localisation
        
        Args:
            location_str: Chaîne contenant la localisation
            
        Returns:
            Dict avec ville et quartier
        """
        result = {'ville': None, 'quartier': None}
        
        if not location_str:
            return result
        
        # Chercher le format "Quartier à Ville (Code postal)"
        match = re.search(r'(.+?)\s+à\s+(.+?)\s*\((\d{5})\)', location_str)
        if match:
            result['quartier'] = match.group(1).strip()
            result['ville'] = match.group(2).strip()
            return result
        
        # Chercher le format "Ville Code postal"
        match = re.search(r'(.+?)\s+(\d{5})', location_str)
        if match:
            result['ville'] = match.group(1).strip()
            return result
        
        # Chercher le format "Ville, arrondissement"
        match = re.search(r'([A-Za-zÀ-ÿ\s-]+),?\s*(\d+(?:er|ème|e)?)?', location_str)
        if match:
            result['ville'] = match.group(1).strip()
            if match.group(2):
                result['quartier'] = match.group(2).strip()
            return result
        
        return result

    def extract_details_from_page(self, url: str) -> Dict:
        """
        Récupère les détails d'une annonce depuis sa page
        
        Args:
            url: URL de l'annonce
            
        Returns:
            Dictionnaire avec les détails extraits
        """
        details = {
            'gps_latitude': None,
            'gps_longitude': None,
            'ville': None,
            'quartier': None,
            'dpe': None,
            'ges': None,
            'images': [],
            'tags': [],  # Ajout des tags/propriétés
            'surface_clean': None,
            'location_clean': None,
            'date_recuperation': datetime.now().isoformat(),
            'date_publication': None,
        }
        
        try:
            self._wait_before_request()
            
            headers = get_realistic_headers()
            headers['Referer'] = 'https://www.seloger.com/'
            
            response = self._s.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"    ⚠️  Erreur HTTP {response.status_code}")
                return details
            
            doc = html.fromstring(response.content)
            
            # 1. Extraire les coordonnées GPS depuis la carte ou les métadonnées
            # Chercher dans le script JSON-LD
            script_json = doc.xpath("//script[@type='application/ld+json']/text()")
            if script_json:
                try:
                    for script in script_json:
                        data = json.loads(script)
                        if isinstance(data, dict) and 'geo' in data:
                            geo = data['geo']
                            details['gps_latitude'] = geo.get('latitude')
                            details['gps_longitude'] = geo.get('longitude')
                        if isinstance(data, dict) and 'address' in data:
                            address = data['address']
                            if isinstance(address, dict):
                                details['ville'] = address.get('addressLocality')
                except json.JSONDecodeError:
                    pass
            
            # Chercher les coordonnées dans les attributs data-* ou dans le code JavaScript
            lat_lon = doc.xpath("//div[@data-latitude and @data-longitude]")
            if lat_lon:
                details['gps_latitude'] = lat_lon[0].get('data-latitude')
                details['gps_longitude'] = lat_lon[0].get('data-longitude')
            
            # Chercher dans le script avec les données de la carte
            map_scripts = doc.xpath("//script[contains(text(), 'latitude') or contains(text(), 'lat')]/text()")
            for script in map_scripts:
                # Chercher pattern: latitude: XX.XXXX ou lat: XX.XXXX
                lat_match = re.search(r'(?:latitude|lat)[\s:]+([0-9.]+)', script)
                lon_match = re.search(r'(?:longitude|lng|lon)[\s:]+([0-9.]+)', script)
                if lat_match and lon_match:
                    details['gps_latitude'] = float(lat_match.group(1))
                    details['gps_longitude'] = float(lon_match.group(1))
                    break
            
            # 2. Extraire ville et quartier
            location_elements = doc.xpath("//h1//text() | //div[contains(@class, 'location')]//text()")
            location_text = ' '.join([t.strip() for t in location_elements if t.strip()])
            
            if location_text:
                loc_info = self.clean_location(location_text)
                if not details['ville']:
                    details['ville'] = loc_info['ville']
                details['quartier'] = loc_info['quartier']
            
            # 3. Extraire DPE et GES depuis la section Performance énergétique
            # Nouveau sélecteur basé sur la structure HTML réelle
            # DPE (Diagnostic de Performance Énergétique)
            dpe_text = doc.xpath(
                "//div[contains(text(), 'Diagnostic de performance énergétique')]"
                "/following-sibling::div//text()[normalize-space()]"
            )
            for text in dpe_text:
                text = str(text).strip()
                # Chercher une lettre isolée A-G
                if len(text) == 1 and text in 'ABCDEFG':
                    details['dpe'] = text
                    break
            
            # GES (Gaz à Effet de Serre)
            ges_text = doc.xpath(
                "//div[contains(text(), \"Indice d'émission de gaz\")]"
                "/following-sibling::div//text()[normalize-space()]"
            )
            for text in ges_text:
                text = str(text).strip()
                if len(text) == 1 and text in 'ABCDEFG':
                    details['ges'] = text
                    break
            
            # Alternative: chercher dans les SVG ou éléments avec la classe energy
            if not details['dpe']:
                dpe_elements = doc.xpath(
                    "//*[contains(@class, 'energy') or contains(@class, 'dpe')]"
                    "//text()[string-length()=1]"
                )
                for text in dpe_elements:
                    if text.strip() in 'ABCDEFG':
                        details['dpe'] = text.strip()
                        break
            
            if not details['ges']:
                ges_elements = doc.xpath(
                    "//*[contains(@class, 'climate') or contains(@class, 'ges')]"
                    "//text()[string-length()=1]"
                )
                for text in ges_elements:
                    if text.strip() in 'ABCDEFG':
                        details['ges'] = text.strip()
                        break
            
            # 4. Extraire les images (visite immersive et galerie)
            # Chercher dans la visite immersive et toutes les images
            img_urls = doc.xpath(
                "//img/@src | "
                "//img/@data-src | "
                "//source/@srcset"
            )
            
            # Nettoyer et dédupliquer les URLs d'images
            seen_images = set()
            for img_url in img_urls:
                if not img_url:
                    continue
                
                # Pour srcset, prendre juste la première URL
                if ' ' in img_url:
                    img_url = img_url.split()[0]
                
                # Ignorer placeholders, icônes et petites images
                if any(x in img_url.lower() for x in [
                    'placeholder', 'icon', 'logo', 'sprite',
                    'avatar', 'badge', 'marker', '1x1'
                ]):
                    continue
                
                if img_url in seen_images:
                    continue
                
                # Convertir en URL absolue si nécessaire
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://www.seloger.com' + img_url
                
                # Ne garder que les vraies images de bonne qualité
                if any(ext in img_url.lower() for ext in [
                    '.jpg', '.jpeg', '.png', '.webp'
                ]):
                    # Filtrer les très petites images (icônes)
                    if not any(size in img_url for size in [
                        '16x16', '32x32', '64x64', 'thumb'
                    ]):
                        details['images'].append(img_url)
                        seen_images.add(img_url)
            
            # 5. Extraire les tags/caractéristiques du logement
            # Chercher dans la section Caractéristiques
            caracteristiques = doc.xpath(
                "//h2[contains(text(), 'Caractéristiques')]"
                "/following-sibling::*//text()[normalize-space()]"
            )
            
            tags = []
            for text in caracteristiques:
                text = str(text).strip()
                if text and len(text) > 2 and text not in tags:
                    # Nettoyer et ajouter les caractéristiques pertinentes
                    if not text.isdigit() and text not in [
                        'Voir les 10 caractéristiques',
                        'Voir plus',
                        'Voir moins'
                    ]:
                        tags.append(text)
            
            details['tags'] = tags[:15]  # Limiter à 15 tags max
            
            # 5. Extraire la date de publication
            # Chercher dans différents formats
            date_elements = doc.xpath(
                "//*[contains(@class, 'date') or contains(@class, 'publication')]//text() | "
                "//time/@datetime | "
                "//*[contains(text(), 'Publié') or contains(text(), 'publié')]//text()"
            )
            
            for date_text in date_elements:
                # Format ISO
                if 'T' in str(date_text) and '-' in str(date_text):
                    try:
                        details['date_publication'] = str(date_text).split('T')[0]
                        break
                    except:
                        pass
                
                # Format français: "Publié le 15/01/2024"
                match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', str(date_text))
                if match:
                    day, month, year = match.groups()
                    details['date_publication'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break
            
            # 6. Extraire la surface proprement
            surface_elements = doc.xpath("//*[contains(text(), 'm²')]//text()")
            for text in surface_elements:
                surface = self.clean_surface(text)
                if surface:
                    details['surface_clean'] = surface
                    break
            
            return details
            
        except Exception as e:
            print(f"    ❌ Erreur lors de l'extraction: {e}")
            return details

    def enrich_annonces(self, annonces: List[Dict]) -> List[Dict]:
        """
        Enrichit une liste d'annonces avec des détails supplémentaires
        
        Args:
            annonces: Liste des annonces à enrichir
            
        Returns:
            Liste des annonces enrichies
        """
        enriched = []
        total = len(annonces)
        
        print(f"\n🔍 Enrichissement de {total} annonces...\n")
        
        for i, annonce in enumerate(annonces, 1):
            print(f"[{i}/{total}] Traitement de l'annonce {annonce.get('id', '?')}...")
            
            url = annonce.get('url')
            if not url:
                print("    ⚠️  Pas d'URL, annonce ignorée")
                enriched.append(annonce)
                continue
            
            # Récupérer les détails
            details = self.extract_details_from_page(url)
            
            # Nettoyer la surface si elle n'est pas déjà propre
            if not details['surface_clean'] and annonce.get('surface'):
                details['surface_clean'] = self.clean_surface(annonce['surface'])
            
            # Nettoyer la localisation si pas déjà fait
            if not details['ville'] and annonce.get('location'):
                loc_info = self.clean_location(annonce['location'])
                details['ville'] = loc_info['ville']
                details['quartier'] = loc_info['quartier']
            
            # Fusionner avec l'annonce existante
            annonce_enriched = {**annonce, **details}
            enriched.append(annonce_enriched)
            
            # Afficher un résumé
            status = []
            if details['gps_latitude'] and details['gps_longitude']:
                status.append(f"📍 GPS: {details['gps_latitude']}, {details['gps_longitude']}")
            if details['ville']:
                status.append(f"🏙️  {details['ville']}")
            if details['quartier']:
                status.append(f"📍 {details['quartier']}")
            if details['dpe']:
                status.append(f"⚡ DPE: {details['dpe']}")
            if details['ges']:
                status.append(f"🌍 GES: {details['ges']}")
            if details['images']:
                status.append(f"🖼️  {len(details['images'])} images")
            if details['surface_clean']:
                status.append(f"📐 {details['surface_clean']} m²")
            if details['date_publication']:
                status.append(f"📅 Pub: {details['date_publication']}")
            
            if status:
                print(f"    ✅ {' | '.join(status)}")
            else:
                print(f"    ⚠️  Peu d'informations récupérées")
            
            # Pause entre les annonces
            if i < total:
                time.sleep(random.uniform(1.5, 3.0))
        
        return enriched

    def save_to_json(self, results: List[Dict], filename: str):
        """
        Sauvegarde les résultats dans un fichier JSON
        
        Args:
            results: Liste des annonces enrichies
            filename: Nom du fichier de sortie
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 {len(results)} annonces enrichies sauvegardées dans {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description='Enrichit les annonces SeLoger avec des détails supplémentaires'
    )
    argparser.add_argument(
        '--input', '-i',
        type=str,
        default='annonces.json',
        help='Fichier JSON d\'entrée avec les annonces (défaut: annonces.json)'
    )
    argparser.add_argument(
        '--output', '-o',
        type=str,
        default='annonces_enriched.json',
        help='Fichier JSON de sortie (défaut: annonces_enriched.json)'
    )
    argparser.add_argument(
        '--cookies', '-c',
        type=str,
        default='.cookies',
        help='Fichier de cookies (défaut: .cookies)'
    )
    argparser.add_argument(
        '--limit', '-l',
        type=int,
        help='Limiter le nombre d\'annonces à traiter (pour tests)'
    )
    
    args = argparser.parse_args()
    
    print("""
╔══════════════════════════════════════════════════════════╗
║      SeLoger Enrichisseur - Détails des Annonces        ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Charger les annonces existantes
    if not os.path.exists(args.input):
        print(f"❌ Fichier d'entrée '{args.input}' non trouvé")
        exit(1)
    
    with open(args.input, 'r', encoding='utf-8') as f:
        annonces = json.load(f)
    
    print(f"📂 {len(annonces)} annonces chargées depuis {args.input}")
    
    # Limiter si demandé
    if args.limit:
        annonces = annonces[:args.limit]
        print(f"⚠️  Limitation à {args.limit} annonces pour ce test")
    
    # Créer l'enrichisseur
    enricher = AnnonceEnricher(cookies_file=args.cookies)
    
    # Enrichir les annonces
    enriched = enricher.enrich_annonces(annonces)
    
    # Sauvegarder les résultats
    if enriched:
        enricher.save_to_json(enriched, args.output)
        print(f"\n✅ Enrichissement terminé avec succès!")
        print(f"📊 {len(enriched)} annonces enrichies")
        
        # Statistiques
        with_gps = sum(1 for a in enriched if a.get('gps_latitude'))
        with_dpe = sum(1 for a in enriched if a.get('dpe'))
        with_images = sum(1 for a in enriched if a.get('images'))
        with_date = sum(1 for a in enriched if a.get('date_publication'))
        
        print(f"\n📈 Statistiques:")
        print(f"   - Coordonnées GPS: {with_gps}/{len(enriched)}")
        print(f"   - DPE: {with_dpe}/{len(enriched)}")
        print(f"   - Images: {with_images}/{len(enriched)}")
        print(f"   - Date publication: {with_date}/{len(enriched)}")
    else:
        print("\n⚠️  Aucune annonce enrichie")
    
    print("""
    
    🦀 lobstr 🦀
    """)
