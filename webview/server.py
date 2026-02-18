#!/usr/bin/env python3
"""
Serveur web simple pour visualiser les annonces immobilières
Usage: python3 server.py [URL_JSON]
"""
import http.server
import socketserver
import os
import sys
import urllib.request
import urllib.error

PORT = 8012
CACHE_FILE = "annonces_cache.json"
DATA_URL = None  # URL configurée via argument en ligne de commande


class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Ajouter les headers CORS pour éviter les problèmes de chargement
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Intercepter les requêtes vers /api/annonces
        if self.path.startswith('/api/annonces'):
            self.serve_annonces()
        else:
            # Servir les fichiers statiques normalement
            super().do_GET()

    def serve_annonces(self):
        """Télécharger et servir les annonces depuis l'URL ou le cache"""
        global DATA_URL
        
        try:
            # Essayer de télécharger depuis l'URL si elle est configurée
            if DATA_URL:
                print(f"📥 Téléchargement des annonces depuis {DATA_URL}...")
                
                with urllib.request.urlopen(DATA_URL, timeout=30) as response:
                    data = response.read()
                    
                # Sauvegarder dans le cache
                with open(CACHE_FILE, 'wb') as f:
                    f.write(data)
                msg = f"Données sauvegardées dans {CACHE_FILE}"
                print(f"✅ {msg}")
                
                # Envoyer les données
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
                
            else:
                # Pas d'URL configurée, essayer le cache
                if os.path.exists(CACHE_FILE):
                    print(f"📂 Chargement depuis le cache {CACHE_FILE}...")
                    with open(CACHE_FILE, 'rb') as f:
                        data = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    msg = (f"Aucune URL configurée et pas de cache "
                           f"trouvé ({CACHE_FILE})")
                    raise FileNotFoundError(msg)
                    
        except urllib.error.URLError as e:
            # Erreur de téléchargement, essayer le cache
            print(f"⚠️ Erreur de téléchargement: {e}")
            if os.path.exists(CACHE_FILE):
                print(f"📂 Utilisation du cache {CACHE_FILE}...")
                with open(CACHE_FILE, 'rb') as f:
                    data = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
            else:
                msg = ("Service indisponible: impossible de télécharger "
                       "et pas de cache")
                self.send_error(503, msg)
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.send_error(500, f"Erreur interne: {str(e)}")

    def log_message(self, format, *args):  # noqa: A002
        # Logger les requêtes
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    global DATA_URL
    
    # Changer le répertoire vers celui du script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Vérifier si une URL est fournie en argument
    if len(sys.argv) > 1:
        DATA_URL = sys.argv[1]
        print(f"🔗 URL configurée: {DATA_URL}")
    else:
        print("ℹ️  Aucune URL fournie, utilisation du cache si disponible")
        print("   Usage: python3 server.py <URL_JSON>")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Serveur démarré sur http://localhost:{PORT}")
        print(f"📂 Répertoire: {os.getcwd()}")
        print(f"💾 Fichier cache: {CACHE_FILE}")
        url = f"http://localhost:{PORT}"
        print(f"🌐 Ouvrez votre navigateur à l'adresse: {url}")
        print("⏹️  Appuyez sur Ctrl+C pour arrêter le serveur\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt du serveur...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
