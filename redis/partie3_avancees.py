"""
PARTIE 3 : Structures avancees et cas limites
Gestion des livreurs multi-regions et cache avec TTL
"""
import redis
import sys
import os
import time

# Ajouter le chemin parent pour importer la config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import REDIS_CONFIG

# Connexion Redis
r = redis.Redis(**REDIS_CONFIG)

def reset_redis():
    """Nettoie toutes les donnees Redis pour recommencer proprement"""
    r.flushdb()
    print("[RESET] Base Redis nettoyee")

def initialiser_donnees_base():
    """Initialise les donnees de base pour les demonstrations"""
    print("\n[INIT] Initialisation des donnees de base")
    
    # Livreurs
    livreurs = [
        {"id": "d1", "nom": "Alice Dupont", "regions": ["Paris", "Banlieue"], "rating": 4.8},
        {"id": "d2", "nom": "Bob Martin", "regions": ["Paris"], "rating": 4.5},
        {"id": "d3", "nom": "Charlie Lefevre", "regions": ["Banlieue"], "rating": 4.9},
        {"id": "d4", "nom": "Diana Russo", "regions": ["Banlieue", "Province"], "rating": 4.3},
        {"id": "d5", "nom": "Eric Blanc", "regions": ["Paris"], "rating": 4.7},
    ]
    
    for livreur in livreurs:
        livreur_id = livreur["id"]
        
        # Stocker les infos de base
        r.hset(f"livreur:{livreur_id}", mapping={
            "nom": livreur["nom"],
            "rating": livreur["rating"]
        })
        
        # Ajouter au classement
        r.zadd("livreurs:ratings", {livreur_id: livreur["rating"]})
        
        print(f"[OK] Livreur {livreur_id} ({livreur['nom']}) initialise")
    
    # Commandes
    commandes = [
        {"id": "c1", "destination": "Marais", "region": "Paris", "statut": "en_attente"},
        {"id": "c2", "destination": "Belleville", "region": "Paris", "statut": "en_attente"},
        {"id": "c3", "destination": "Neuilly", "region": "Banlieue", "statut": "en_attente"},
        {"id": "c4", "destination": "Versailles", "region": "Banlieue", "statut": "en_attente"},
    ]
    
    for commande in commandes:
        commande_id = commande["id"]
        r.hset(f"commande:{commande_id}", mapping={
            "destination": commande["destination"],
            "region": commande["region"],
            "statut": commande["statut"]
        })
        r.sadd(f"commandes:{commande['statut']}", commande_id)
        r.sadd(f"commandes:region:{commande['region']}", commande_id)
        print(f"[OK] Commande {commande_id} ({commande['destination']}) initialisee")

def travail1_livreurs_multi_regions():
    """
    Travail 1 : Gestion des livreurs multi-regions
    
    Structure proposee :
    - Set pour chaque region : livreurs:region:{region_name}
    - Hash pour chaque livreur avec liste de regions
    """
    print("\n\n[TRAVAIL 1] Gestion des livreurs multi-regions")
    
    # Configuration des regions par livreur
    config_regions = {
        "d1": ["Paris", "Banlieue"],
        "d2": ["Paris"],
        "d3": ["Banlieue"],
        "d4": ["Banlieue", "Province"],
        "d5": ["Paris"]
    }
    
    print("\nConfiguration des regions par livreur :")
    for livreur_id, regions in config_regions.items():
        nom = r.hget(f"livreur:{livreur_id}", "nom")
        
        # Stocker les regions dans le hash du livreur
        r.hset(f"livreur:{livreur_id}", "regions", ",".join(regions))
        
        # Ajouter le livreur dans les sets de chaque region
        for region in regions:
            r.sadd(f"livreurs:region:{region}", livreur_id)
        
        print(f"  {livreur_id} ({nom}): {', '.join(regions)}")
    
    # Demonstration : Trouver tous les livreurs operant a Paris
    print("\n--- Demonstration ---")
    print("\nLivreurs operant a Paris :")
    livreurs_paris = r.smembers("livreurs:region:Paris")
    for lid in livreurs_paris:
        nom = r.hget(f"livreur:{lid}", "nom")
        regions = r.hget(f"livreur:{lid}", "regions")
        rating = r.hget(f"livreur:{lid}", "rating")
        print(f"  - {lid}: {nom} (Rating: {rating}) - Regions: {regions}")
    
    print("\nLivreurs operant en Banlieue :")
    livreurs_banlieue = r.smembers("livreurs:region:Banlieue")
    for lid in livreurs_banlieue:
        nom = r.hget(f"livreur:{lid}", "nom")
        regions = r.hget(f"livreur:{lid}", "regions")
        rating = r.hget(f"livreur:{lid}", "rating")
        print(f"  - {lid}: {nom} (Rating: {rating}) - Regions: {regions}")
    
    # Livreurs operant dans plusieurs regions
    print("\nLivreurs multi-regions :")
    for livreur_id, regions in config_regions.items():
        if len(regions) > 1:
            nom = r.hget(f"livreur:{livreur_id}", "nom")
            rating = r.hget(f"livreur:{livreur_id}", "rating")
            print(f"  - {livreur_id}: {nom} (Rating: {rating}) - {len(regions)} regions: {', '.join(regions)}")

def travail2_cache_avec_ttl():
    """
    Travail 2 : Cache temps reel avec expiration automatique (TTL)
    
    Caches :
    1. Top 5 livreurs par rating (TTL: 30s)
    2. Commandes en attente par region (TTL: 30s)
    """
    print("\n\n[TRAVAIL 2] Cache avec expiration (TTL)")
    
    TTL = 30  # Temps d'expiration en secondes
    
    # Cache 1 : Top 5 livreurs par rating
    print("\n--- Cache 1 : Top 5 livreurs par rating ---")
    
    cache_key = "cache:top_livreurs"
    
    # Creer le cache
    top_livreurs = r.zrevrange("livreurs:ratings", 0, 4, withscores=True)
    
    # Stocker dans un hash avec TTL
    cache_data = {}
    for livreur_id, rating in top_livreurs:
        nom = r.hget(f"livreur:{livreur_id}", "nom")
        cache_data[livreur_id] = f"{nom} ({rating})"
    
    if cache_data:
        r.hset(cache_key, mapping=cache_data)
        r.expire(cache_key, TTL)
        print(f"[OK] Cache cree avec TTL de {TTL}s")
        
        # Afficher le contenu du cache
        print("\nContenu du cache :")
        for livreur_id, info in cache_data.items():
            print(f"  - {livreur_id}: {info}")
        
        # Afficher le TTL
        ttl_restant = r.ttl(cache_key)
        print(f"\nTTL restant : {ttl_restant}s")
    
    # Cache 2 : Commandes en attente par region
    print("\n\n--- Cache 2 : Commandes en attente par region ---")
    
    regions = ["Paris", "Banlieue"]
    
    for region in regions:
        cache_key = f"cache:commandes_attente:{region}"
        
        # Recuperer les commandes en attente de cette region
        commandes = r.smembers(f"commandes:region:{region}")
        commandes_attente = []
        
        for cid in commandes:
            statut = r.hget(f"commande:{cid}", "statut")
            if statut == "en_attente":
                destination = r.hget(f"commande:{cid}", "destination")
                commandes_attente.append(f"{cid}:{destination}")
        
        if commandes_attente:
            # Stocker dans une liste avec TTL
            r.delete(cache_key)  # Supprimer l'ancien cache si existe
            r.rpush(cache_key, *commandes_attente)
            r.expire(cache_key, TTL)
            
            print(f"\n[OK] Cache pour {region} cree avec TTL de {TTL}s")
            print(f"Commandes en attente a {region} :")
            for cmd in commandes_attente:
                print(f"  - {cmd}")
            
            ttl_restant = r.ttl(cache_key)
            print(f"TTL restant : {ttl_restant}s")
    
    # Principe de fonctionnement
    print("\n\n--- Principe de fonctionnement ---")
    print("1. Les caches sont crees avec une expiration automatique (TTL)")
    print("2. Apres 30 secondes, Redis supprime automatiquement les cles")
    print("3. L'application doit regenerer le cache si la cle n'existe plus")
    print("4. Commande pour verifier l'existence : EXISTS cache:top_livreurs")
    print("5. Commande pour verifier le TTL : TTL cache:top_livreurs")
    
    # Demonstration de verification
    print("\n--- Verification de l'existence des caches ---")
    cache_keys = ["cache:top_livreurs", "cache:commandes_attente:Paris", "cache:commandes_attente:Banlieue"]
    
    for key in cache_keys:
        existe = r.exists(key)
        if existe:
            ttl = r.ttl(key)
            print(f"{key}: EXISTS (TTL: {ttl}s)")
        else:
            print(f"{key}: N'EXISTE PAS")
    
    # Fonction de reactualisation du cache
    print("\n--- Fonction de reactualisation ---")
    print("""
def reactualiser_cache_top_livreurs():
    cache_key = "cache:top_livreurs"
    
    # Verifier si le cache existe
    if not r.exists(cache_key):
        print("[CACHE MISS] Regeneration du cache...")
        
        # Regenerer le cache
        top_livreurs = r.zrevrange("livreurs:ratings", 0, 4, withscores=True)
        cache_data = {}
        for livreur_id, rating in top_livreurs:
            nom = r.hget(f"livreur:{{livreur_id}}", "nom")
            cache_data[livreur_id] = f"{{nom}} ({{rating}})"
        
        r.hset(cache_key, mapping=cache_data)
        r.expire(cache_key, 30)
        return cache_data
    else:
        print("[CACHE HIT] Lecture depuis le cache...")
        return r.hgetall(cache_key)
    """)

if __name__ == "__main__":
    # Nettoyer Redis
    reset_redis()
    
    # Initialiser les donnees
    initialiser_donnees_base()
    
    # Executer les travaux
    travail1_livreurs_multi_regions()
    travail2_cache_avec_ttl()
    
    print("\n\n[FIN] Partie 3 terminee")