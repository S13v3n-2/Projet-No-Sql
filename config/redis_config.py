"""
Configuration Redis - NE PAS METTRE DE PASSWORDS ICI !
Utiliser .env pour psw
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'password': os.getenv('REDIS_PASSWORD', ''),
    'decode_responses': True
}