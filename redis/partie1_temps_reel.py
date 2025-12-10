"""
PARTIE 1 : Etat temps reel avec Redis
Gestion des livreurs et commandes en temps reel
"""
import redis
import sys
import os

# Ajouter le chemin parent pour importer la config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.redis_config import REDIS_CONFIG

# Connexion Redis
r = redis.Redis(**REDIS_CONFIG)

def reset_redis():
    """Nettoie toutes les donnees Redis pour recommencer proprement"""
    r.flushdb()
    print("[RESET] Base Redis nettoyee")

def travail1_initialiser_livreurs():
    """
    Travail 1 : Initialiser les livreurs dans Redis
    
    Structures utilisees :
    1. Hash pour chaque livreur : livreur:{id} contenant toutes ses infos
    2. Sorted Set pour le classement par rating : livreurs:ratings
    3. Set pour liste rapide de tous les livreurs : livreurs:all
    """
    print("\n[TRAVAIL 1] Initialiser les livreurs")
    
    # Donnees des livreurs
    livreurs = [
        {"id": "d1", "nom": "Alice Dupont", "region": "Paris", "rating": 4.8},
        {"id": "d2", "nom": "Bob Martin", "region": "Paris", "rating": 4.5},
        {"id": "d3", "nom": "Charlie Lefevre", "region": "Banlieue", "rating": 4.9},
        {"id": "d4", "nom": "Diana Russo", "region": "Banlieue", "rating": 4.3},
        {"id": "d5", "nom": "Eric Blanc", "region": "Paris", "rating": 4.7},
        {"id": "d6", "nom": "Fanny Moreau", "region": "Banlieue", "rating": 4.6},
    ]
    
    for livreur in livreurs:
        livreur_id = livreur["id"]
        
        # 1. Stocker les infos du livreur dans un Hash
        r.hset(f"livreur:{livreur_id}", mapping={
            "nom": livreur["nom"],
            "region": livreur["region"],
            "rating": livreur["rating"],
            "livraisons_en_cours": 0,
            "livraisons_completees": 0
        })
        
        # 2. Ajouter au Sorted Set pour classement par rating
        r.zadd("livreurs:ratings", {livreur_id: livreur["rating"]})
        
        # 3. Ajouter au Set de tous les livreurs
        r.sadd("livreurs:all", livreur_id)
        
        print(f"[OK] Livreur {livreur_id} ({livreur['nom']}) initialise - Rating: {livreur['rating']}")
    
    print(f"\n[TOTAL] {len(livreurs)} livreurs initialises")
    
    # Demonstration des requetes
    print("\n--- Demonstrations ---")
    
    # Acces rapide au rating d'un livreur
    rating_d1 = r.hget("livreur:d1", "rating")
    print(f"\n1. Rating du livreur d1 : {rating_d1}")
    
    # Liste de tous les livreurs avec leur rating
    print("\n2. Liste de tous les livreurs avec rating :")
    tous_livreurs = r.smembers("livreurs:all")
    for lid in tous_livreurs:
        nom = r.hget(f"livreur:{lid}", "nom")
        rating = r.hget(f"livreur:{lid}", "rating")
        print(f"   - {lid}: {nom} (Rating: {rating})")
    
    # Meilleurs livreurs (rating >= 4.7)
    print("\n3. Meilleurs livreurs (rating >= 4.7) :")
    meilleurs = r.zrangebyscore("livreurs:ratings", 4.7, 5.0, withscores=True)
    for livreur_id, rating in meilleurs:
        nom = r.hget(f"livreur:{livreur_id}", "nom")
        print(f"   - {livreur_id}: {nom} (Rating: {rating})")

def travail2_gerer_commandes():
    """
    Travail 2 : Gerer les commandes en cours
    
    Structures utilisees :
    1. Hash pour chaque commande : commande:{id} contenant toutes ses infos
    2. Set par statut : commandes:en_attente, commandes:assignee, commandes:livree
    3. Set global : commandes:all
    """
    print("\n\n[TRAVAIL 2] Gerer les commandes en cours")
    
    # Donnees des commandes
    commandes = [
        {"id": "c1", "client": "Client A", "destination": "Marais", "montant": 25, "heure": "14:00"},
        {"id": "c2", "client": "Client B", "destination": "Belleville", "montant": 15, "heure": "14:05"},
        {"id": "c3", "client": "Client C", "destination": "Bercy", "montant": 30, "heure": "14:10"},
        {"id": "c4", "client": "Client D", "destination": "Auteuil", "montant": 20, "heure": "14:15"},
        {"id": "c5", "client": "Client E", "destination": "Bastille", "montant": 18, "heure": "14:20"},
        {"id": "c6", "client": "Client F", "destination": "Montmartre", "montant": 22, "heure": "14:25"},
    ]
    
    for commande in commandes:
        commande_id = commande["id"]
        
        # 1. Stocker les infos de la commande dans un Hash
        r.hset(f"commande:{commande_id}", mapping={
            "client": commande["client"],
            "destination": commande["destination"],
            "montant": commande["montant"],
            "heure_creation": commande["heure"],
            "statut": "en_attente"
        })
        
        # 2. Ajouter au Set des commandes en attente
        r.sadd("commandes:en_attente", commande_id)
        
        # 3. Ajouter au Set global
        r.sadd("commandes:all", commande_id)
        
        print(f"[OK] Commande {commande_id} initialisee - {commande['destination']} - {commande['montant']}EUR - Statut: en_attente")
    
    print(f"\n[TOTAL] {len(commandes)} commandes initialisees")
    
    # Demonstration
    print("\n--- Demonstrations ---")
    
    # Nombre de commandes par statut
    nb_en_attente = r.scard("commandes:en_attente")
    nb_assignee = r.scard("commandes:assignee")
    nb_livree = r.scard("commandes:livree")
    
    print(f"\n1. Nombre de commandes par statut :")
    print(f"   - En attente : {nb_en_attente}")
    print(f"   - Assignees : {nb_assignee}")
    print(f"   - Livrees : {nb_livree}")
    
    # Liste des commandes en attente
    print(f"\n2. Liste des commandes en attente :")
    commandes_attente = r.smembers("commandes:en_attente")
    for cid in commandes_attente:
        client = r.hget(f"commande:{cid}", "client")
        destination = r.hget(f"commande:{cid}", "destination")
        montant = r.hget(f"commande:{cid}", "montant")
        print(f"   - {cid}: {client} -> {destination} ({montant}EUR)")

def travail3_affecter_commande():
    """
    Travail 3 : Affecter une commande a un livreur de maniere atomique
    
    Operations atomiques :
    1. Changer le statut de la commande (en_attente -> assignee)
    2. Enregistrer l'affectation (quelle commande a quel livreur)
    3. Incrementer le compteur de livraisons en cours du livreur
    
    Utilisation d'une transaction Redis (MULTI/EXEC) pour garantir l'atomicite
    """
    print("\n\n[TRAVAIL 3] Affecter une commande a un livreur (atomique)")
    
    commande_id = "c1"
    livreur_id = "d3"
    
    print(f"\nAffectation de la commande {commande_id} au livreur {livreur_id}")
    
    # Verification avant affectation
    statut_avant = r.hget(f"commande:{commande_id}", "statut")
    livraisons_avant = r.hget(f"livreur:{livreur_id}", "livraisons_en_cours")
    print(f"[AVANT] Statut commande: {statut_avant}, Livraisons en cours livreur: {livraisons_avant}")
    
    # Transaction atomique avec pipeline
    pipe = r.pipeline()
    
    # 1. Mettre a jour le statut de la commande
    pipe.hset(f"commande:{commande_id}", "statut", "assignee")
    pipe.hset(f"commande:{commande_id}", "livreur_id", livreur_id)
    
    # 2. Deplacer la commande dans le bon set de statut
    pipe.srem("commandes:en_attente", commande_id)
    pipe.sadd("commandes:assignee", commande_id)
    
    # 3. Enregistrer l'affectation
    pipe.sadd(f"livreur:{livreur_id}:commandes", commande_id)
    
    # 4. Incrementer le compteur de livraisons en cours
    pipe.hincrby(f"livreur:{livreur_id}", "livraisons_en_cours", 1)
    
    # Executer la transaction
    pipe.execute()
    
    print("[OK] Transaction executee avec succes")
    
    # Verification apres affectation
    statut_apres = r.hget(f"commande:{commande_id}", "statut")
    livreur_affecte = r.hget(f"commande:{commande_id}", "livreur_id")
    livraisons_apres = r.hget(f"livreur:{livreur_id}", "livraisons_en_cours")
    
    print(f"[APRES] Statut commande: {statut_apres}, Livreur affecte: {livreur_affecte}, Livraisons en cours: {livraisons_apres}")
    
    # Demonstration
    print("\n--- Demonstrations ---")
    
    # Commandes assignees au livreur d3
    commandes_d3 = r.smembers(f"livreur:{livreur_id}:commandes")
    print(f"\n1. Commandes assignees au livreur {livreur_id}: {commandes_d3}")
    
    # Nombre de commandes par statut
    nb_en_attente = r.scard("commandes:en_attente")
    nb_assignee = r.scard("commandes:assignee")
    print(f"\n2. Commandes en attente: {nb_en_attente}, Commandes assignees: {nb_assignee}")

if __name__ == "__main__":
    # Nettoyer Redis avant de commencer
    reset_redis()
    
    # Executer les travaux
    travail1_initialiser_livreurs()
    travail2_gerer_commandes()
    travail3_affecter_commande()