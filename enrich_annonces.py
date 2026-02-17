#!/usr/bin/env python3
"""
Script d'enrichissement des annonces SeLoger avec Selenium
Extrait: images, tags, DPE, GES, localisation
"""

import json
import argparse
import time
import random
import os
import re
from datetime import datetime
from typing import Dict
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def init_driver():
    """Initialise le driver Selenium"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", 
                                          ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # Charger les cookies
    driver.get("https://www.seloger.com")
    time.sleep(2)
    
    if os.path.exists('.cookies'):
        with open('.cookies', 'r') as f:
            cookies_data = json.load(f)
            if isinstance(cookies_data, dict):
                for name, value in cookies_data.items():
                    driver.add_cookie({
                        'name': name,
                        'value': value,
                        'domain': '.seloger.com'
                    })
    
    return driver


def extract_details(driver, url: str) -> Dict:
    """Extrait les détails d'une annonce"""
    details = {
        'gps_latitude': None,
        'gps_longitude': None,
        'ville': None,
        'quartier': None,
        'dpe': None,
        'ges': None,
        'images': [],
        'tags': [],
        'surface_clean': None,
        'location_clean': None,
        'date_recuperation': datetime.now().isoformat(),
        'date_publication': None,
    }
    
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        time.sleep(3)
        
        page_source = driver.page_source
        doc = html.fromstring(page_source.encode('utf-8'))
        
        # Extraire les tags/caractéristiques
        carac_section = doc.xpath(
            "//h2[contains(text(), 'Caractéristiques')]"
            "/following-sibling::ul//li//text()[normalize-space()]"
        )
        tags = []
        for text in carac_section:
            text = str(text).strip()
            if text and len(text) > 1 and text not in tags:
                if text not in ['Voir', 'plus', 'moins', 'caractéristiques']:
                    tags.append(text)
        details['tags'] = tags[:15]
        
        # Extraire les images
        img_urls = doc.xpath("//img/@src")
        seen_images = set()
        for img_url in img_urls:
            if not img_url or 'placeholder' in img_url.lower():
                continue
            if 'icon' in img_url.lower() or 'logo' in img_url.lower():
                continue
            if img_url in seen_images:
                continue
                
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                img_url = 'https://www.seloger.com' + img_url
            
            if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                details['images'].append(img_url)
                seen_images.add(img_url)
        
        # Extraire DPE
        dpe_section = doc.xpath(
            "//h3[contains(text(), 'Diagnostic de Performance')]"
            "/following-sibling::div//text()[normalize-space()]"
        )
        for text in dpe_section:
            text = str(text).strip()
            if len(text) == 1 and text in 'ABCDEFG':
                details['dpe'] = text
                break
            match = re.search(r'\b([A-G])\b', text)
            if match:
                details['dpe'] = match.group(1)
                break
        
        # Extraire GES
        ges_section = doc.xpath(
            "//h3[contains(text(), 'mission') or contains(text(), 'GES')]"
            "/following-sibling::div//text()[normalize-space()]"
        )
        for text in ges_section:
            text = str(text).strip()
            if len(text) == 1 and text in 'ABCDEFG':
                details['ges'] = text
                break
            match = re.search(r'\b([A-G])\b', text)
            if match:
                details['ges'] = match.group(1)
                break
        
        # Extraire localisation
        h1_texts = doc.xpath("//h1//text()")
        location_text = ' '.join([t.strip() for t in h1_texts if t.strip()])
        match = re.search(r'([A-ZÀ-ÿ][a-zà-ÿ\s-]+)\s+(\d+(?:er|ème)?)', 
                         location_text)
        if match:
            details['ville'] = match.group(1).strip()
            details['quartier'] = match.group(2).strip()
        
        return details
        
    except Exception as e:
        print(f"    ⚠️  Erreur: {e}")
        return details


def main():
    parser = argparse.ArgumentParser(
        description='Enrichit les annonces SeLoger'
    )
    parser.add_argument('--input', default='annonces.json',
                       help='Fichier JSON d\'entrée')
    parser.add_argument('--output', default='annonces_enriched.json',
                       help='Fichier JSON de sortie')
    parser.add_argument('--limit', type=int,
                       help='Nombre max d\'annonces à traiter')
    
    args = parser.parse_args()
    
    print('\n╔══════════════════════════════════════════════════════════╗')
    print('║      SeLoger Enrichisseur - Détails des Annonces        ║')
    print('╚══════════════════════════════════════════════════════════╝\n')
    
    # Charger les annonces
    with open(args.input, 'r', encoding='utf-8') as f:
        annonces = json.load(f)
    
    print(f'📂 {len(annonces)} annonces chargées depuis {args.input}')
    
    if args.limit:
        annonces = annonces[:args.limit]
        print(f'⚠️  Limitation à {len(annonces)} annonces')
    
    print('🌐 Initialisation du navigateur...')
    driver = init_driver()
    print('✅ Navigateur prêt\n')
    print(f'🔍 Enrichissement de {len(annonces)} annonces...\n')
    
    enriched = []
    for i, annonce in enumerate(annonces, 1):
        print(f"[{i}/{len(annonces)}] {annonce.get('url', '?')}...")
        details = extract_details(driver, annonce['url'])
        enriched_annonce = {**annonce, **details}
        enriched.append(enriched_annonce)
        
        ville = details['ville'] or 'N/A'
        quartier = details['quartier'] or 'N/A'
        n_images = len(details['images'])
        n_tags = len(details['tags'])
        print(f"    ✅ {ville} | {quartier} | {n_images} img | {n_tags} tags")
        
        if i < len(annonces):
            time.sleep(random.uniform(2, 4))
    
    driver.quit()
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    
    print(f'\n💾 {len(enriched)} annonces sauvegardées dans {args.output}')
    
    # Statistiques
    stats = {
        'gps': sum(1 for a in enriched if a['gps_latitude']),
        'dpe': sum(1 for a in enriched if a['dpe']),
        'images': sum(1 for a in enriched if a['images']),
        'tags': sum(1 for a in enriched if a['tags']),
    }
    
    print('\n📈 Statistiques:')
    print(f"   - Coordonnées GPS: {stats['gps']}/{len(enriched)}")
    print(f"   - DPE: {stats['dpe']}/{len(enriched)}")
    print(f"   - Images: {stats['images']}/{len(enriched)}")
    print(f"   - Tags: {stats['tags']}/{len(enriched)}")
    
    print('\n✅ Enrichissement terminé!\n')


if __name__ == '__main__':
    main()
