"""
Test de connexion à Redis Cloud
"""
import redis
import sys
import os

# Ajouter le chemin parent pour importer la config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import REDIS_CONFIG

def test_connection():
    """Teste la connexion à Redis Cloud"""
    try:
        # Connexion à Redis
        redis_client = redis.Redis(**REDIS_CONFIG)
        
        # Test ping
        redis_client.ping()
        print("[SUCCESS] Connexion a Redis Cloud reussie")
        
        # Test lecture/écriture
        redis_client.set('test_project', 'Hello from Projet NoSQL')
        value = redis_client.get('test_project')
        print(f"[TEST] Lecture/ecriture : {value}")
        
        # Afficher les infos de connexion (sans le password)
        print(f"\n[INFO] Connecte a : {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
        
        # Nettoyer le test
        redis_client.delete('test_project')
        print("\n[CLEANUP] Test nettoye")
        
        return True
        
    except redis.exceptions.AuthenticationError:
        print("[ERROR] Erreur d'authentification : Verifie ton REDIS_PASSWORD dans .env")
        return False
        
    except redis.exceptions.ConnectionError as e:
        print(f"[ERROR] Erreur de connexion : {e}")
        print("\n[HELP] Verifie :")
        print("   - Ton REDIS_HOST dans .env")
        print("   - Ton REDIS_PORT dans .env")
        print("   - Ta connexion Internet")
        return False
        
    except Exception as e:
        print(f"[ERROR] Erreur inattendue : {e}")
        return False

if __name__ == "__main__":
    test_connection()