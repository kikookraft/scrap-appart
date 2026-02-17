#!/usr/bin/env python3
"""
Script pour extraire automatiquement les cookies SeLoger avec Selenium
L'utilisateur navigue manuellement, puis les cookies sont sauvegardés
"""

import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class CookieExtractor:
    """Extracteur de cookies avec Selenium"""
    
    def __init__(self):
        """Initialise le navigateur Chrome"""
        print("🌐 Initialisation du navigateur Chrome...")
        
        # Configuration de Chrome
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Décommenter pour mode sans interface
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # Initialiser le driver
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            print("✅ Navigateur Chrome lancé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors du lancement de Chrome: {e}")
            print("💡 Installez les dépendances: pip install selenium webdriver-manager")
            raise
        
        self.driver.maximize_window()
    
    def navigate_to_seloger(self):
        """Navigue vers SeLoger"""
        print("\n🔗 Navigation vers SeLoger...")
        self.driver.get("https://www.seloger.com")
        print("✅ Page SeLoger chargée")
    
    def wait_for_user_interaction(self):
        """Attend que l'utilisateur navigue et se connecte"""
        print("\n" + "=" * 60)
        print("👤 À VOUS DE JOUER !")
        print("=" * 60)
        print("""
Instructions :
1. 🔍 Faites votre recherche (Lyon, critères, etc.)
2. 📋 Attendez que les résultats s'affichent
3. ✅ Acceptez les cookies si demandé
4. 🔑 Connectez-vous si nécessaire
5. ⏱️  Attendez quelques secondes sur la page de résultats

Quand vous avez terminé :
➡️  Revenez dans ce terminal et appuyez sur ENTRÉE
        """)
        
        input("Appuyez sur ENTRÉE quand vous êtes prêt à extraire les cookies... ")
    
    def extract_cookies(self):
        """Extrait tous les cookies du navigateur"""
        print("\n🍪 Extraction des cookies...")
        
        cookies = self.driver.get_cookies()
        
        if not cookies:
            print("❌ Aucun cookie trouvé !")
            return None
        
        print(f"✅ {len(cookies)} cookies extraits")
        
        # Afficher les cookies importants
        important_cookies = ['datadome', 'visitId', '_ga', '_gid', 'euconsent-v2']
        print("\n📋 Cookies critiques détectés :")
        for cookie in cookies:
            if cookie['name'] in important_cookies:
                value_preview = cookie['value'][:20] + "..." if len(cookie['value']) > 20 else cookie['value']
                print(f"   ✅ {cookie['name']}: {value_preview}")
        
        return cookies
    
    def save_cookies_simple_format(self, cookies, filename='.cookies'):
        """Sauvegarde les cookies au format simple (dictionnaire)"""
        print(f"\n💾 Sauvegarde au format simple dans {filename}...")
        
        # Format simple : {nom: valeur}
        cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cookies_dict, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookies sauvegardés : {len(cookies_dict)} entrées")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
            return False
    
    def save_cookies_full_format(self, cookies, filename='.cookies.full'):
        """Sauvegarde les cookies au format complet (avec métadonnées)"""
        print(f"\n💾 Sauvegarde au format complet dans {filename}...")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            print(f"✅ Cookies complets sauvegardés")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
            return False
    
    def verify_cookies(self):
        """Vérifie que les cookies critiques sont présents"""
        print("\n🔍 Vérification des cookies critiques...")
        
        try:
            with open('.cookies', 'r') as f:
                cookies_data = json.load(f)
            
            critical = ['datadome', 'visitId', '_ga']
            missing = []
            
            for cookie_name in critical:
                if cookie_name in cookies_data:
                    print(f"   ✅ {cookie_name}")
                else:
                    print(f"   ❌ {cookie_name} MANQUANT")
                    missing.append(cookie_name)
            
            if missing:
                print(f"\n⚠️  Cookies manquants : {', '.join(missing)}")
                print("💡 Essayez de faire une recherche sur SeLoger avant d'extraire")
                return False
            else:
                print("\n✅ Tous les cookies critiques sont présents !")
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification : {e}")
            return False
    
    def close(self):
        """Ferme le navigateur"""
        print("\n🔒 Fermeture du navigateur...")
        self.driver.quit()
        print("✅ Navigateur fermé")


def main():
    """Fonction principale"""
    print("""
╔══════════════════════════════════════════════════════════╗
║     Extracteur de Cookies SeLoger avec Selenium         ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    extractor = None
    
    try:
        # Créer l'extracteur
        extractor = CookieExtractor()
        
        # Naviguer vers SeLoger
        extractor.navigate_to_seloger()
        
        # Attendre l'interaction utilisateur
        extractor.wait_for_user_interaction()
        
        # Extraire les cookies
        cookies = extractor.extract_cookies()
        
        if not cookies:
            print("\n❌ Échec de l'extraction des cookies")
            return
        
        # Sauvegarder au format simple
        if extractor.save_cookies_simple_format(cookies):
            # Sauvegarder aussi le format complet (backup)
            extractor.save_cookies_full_format(cookies)
            
            # Vérifier
            if extractor.verify_cookies():
                print("\n" + "=" * 60)
                print("🎉 SUCCÈS ! Cookies extraits et vérifiés")
                print("=" * 60)
                print("\nVous pouvez maintenant :")
                print("  1. Lancer le scraper : python3 scrap.py")
                print("  2. Tester les cookies : python3 diagnostic_bot.py")
                print("\n💡 Les cookies sont valides pendant ~1 heure")
            else:
                print("\n⚠️  Cookies sauvegardés mais incomplets")
                print("💡 Recommandation : Recommencez et faites une recherche sur SeLoger")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
    
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Toujours fermer le navigateur
        if extractor:
            extractor.close()
        
        print("\n🦀 Au revoir ! 🦀")


if __name__ == "__main__":
    main()
