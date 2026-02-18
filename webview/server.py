#!/usr/bin/env python3
"""
Serveur web simple pour visualiser les annonces immobilières
Usage: python3 server.py
"""
import http.server
import socketserver
import os

PORT = 8012

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Ajouter les headers CORS pour éviter les problèmes de chargement
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # Logger les requêtes
        print(f"[{self.log_date_time_string()}] {format % args}")

def main():
    # Changer le répertoire vers celui du script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Serveur démarré sur http://localhost:{PORT}")
        print(f"📂 Répertoire: {os.getcwd()}")
        print(f"🌐 Ouvrez votre navigateur à l'adresse: http://localhost:{PORT}")
        print(f"⏹️  Appuyez sur Ctrl+C pour arrêter le serveur\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt du serveur...")
            httpd.shutdown()

if __name__ == "__main__":
    main()
