from datetime import datetime
import sys
import os

# Ajouter le répertoire parent au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config.mongodb_config import get_database

def get_deliveries_collection():
    """Retourne la collection deliveries"""
    db = get_database()
    return db["deliveries"]

# ===== TRAVAIL 1 : Importer l'historique =====
def import_initial_history():
    """Insère les livraisons initiales dans MongoDB"""
    collection = get_deliveries_collection()
    
    # Vider la collection pour éviter les doublons
    collection.delete_many({})
    
    deliveries = [
        {
            "command_id": "c1",
            "client": "Client A",
            "driver_id": "d3",
            "driver_name": "Charlie Lefevre",
            "pickup_time": datetime(2025, 12, 6, 14, 5, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 25, 0),
            "duration_minutes": 20,
            "amount": 25,
            "region": "Paris",
            "rating": 4.9,
            "review": "Excellent service, très rapide!",
            "status": "completed"
        },
        {
            "command_id": "c2",
            "client": "Client B",
            "driver_id": "d1",
            "driver_name": "Alice Dupont",
            "pickup_time": datetime(2025, 12, 6, 14, 10, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 25, 0),
            "duration_minutes": 15,
            "amount": 15,
            "region": "Paris",
            "rating": 4.8,
            "review": "Parfait, rien à redire",
            "status": "completed"
        },
        {
            "command_id": "c3",
            "client": "Client C",
            "driver_id": "d2",
            "driver_name": "Bob Martin",
            "pickup_time": datetime(2025, 12, 6, 14, 15, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 40, 0),
            "duration_minutes": 25,
            "amount": 30,
            "region": "Banlieue",
            "rating": 4.5,
            "review": "Bien mais un peu long",
            "status": "completed"
        },
        {
            "command_id": "c4",
            "client": "Client D",
            "driver_id": "d1",
            "driver_name": "Alice Dupont",
            "pickup_time": datetime(2025, 12, 6, 14, 20, 0),
            "delivery_time": datetime(2025, 12, 6, 14, 38, 0),
            "duration_minutes": 18,
            "amount": 20,
            "region": "Paris",
            "rating": 4.8,
            "review": "Toujours aussi efficace!",
            "status": "completed"
        },
        # Ajouter plus de livraisons pour enrichir les analyses
        {
            "command_id": "c5",
            "client": "Client E",
            "driver_id": "d2",
            "driver_name": "Bob Martin",
            "pickup_time": datetime(2025, 12, 6, 15, 0, 0),
            "delivery_time": datetime(2025, 12, 6, 15, 22, 0),
            "duration_minutes": 22,
            "amount": 28,
            "region": "Paris",
            "rating": 4.6,
            "review": "Bon service dans l'ensemble",
            "status": "completed"
        },
        {
            "command_id": "c6",
            "client": "Client F",
            "driver_id": "d3",
            "driver_name": "Charlie Lefevre",
            "pickup_time": datetime(2025, 12, 6, 15, 10, 0),
            "delivery_time": datetime(2025, 12, 6, 15, 28, 0),
            "duration_minutes": 18,
            "amount": 22,
            "region": "Banlieue",
            "rating": 4.9,
            "review": "Impeccable comme toujours",
            "status": "completed"
        }
    ]
    
    result = collection.insert_many(deliveries)
    print(f"✓ {len(result.inserted_ids)} livraisons insérées avec succès!")
    return result

# ===== TRAVAIL 2 : Historique d'un livreur =====
def get_driver_history(driver_id):
    """Affiche toutes les livraisons d'un livreur"""
    collection = get_deliveries_collection()
    deliveries = list(collection.find({"driver_id": driver_id}))
    
    print(f"\n=== Livraisons du livreur {driver_id} ===")
    for delivery in deliveries:
        print(f"  • {delivery['command_id']}: {delivery['client']} - {delivery['amount']}€ (rating: {delivery['rating']})")
    
    return deliveries

def get_driver_stats(driver_id):
    """Calcule le nombre et montant total des livraisons d'un livreur"""
    collection = get_deliveries_collection()
    
    pipeline = [
        {"$match": {"driver_id": driver_id}},
        {"$group": {
            "_id": None,
            "count": {"$sum": 1},
            "total_amount": {"$sum": "$amount"}
        }}
    ]
    
    result = list(collection.aggregate(pipeline))
    
    if result:
        stats = result[0]
        print(f"\n=== Statistiques du livreur {driver_id} ===")
        print(f"  Nombre de livraisons: {stats['count']}")
        print(f"  Montant total: {stats['total_amount']}€")
        return stats
    else:
        print(f"Aucune livraison pour {driver_id}")
        return None

# ===== TRAVAIL 3 : Agrégation - Performance par région =====
def get_region_performance():
    """Affiche les performances par région"""
    collection = get_deliveries_collection()
    
    pipeline = [
        {
            "$group": {
                "_id": "$region",
                "nb_livraisons": {"$sum": 1},
                "revenu_total": {"$sum": "$amount"},
                "duree_moyenne": {"$avg": "$duration_minutes"},
                "rating_moyen": {"$avg": "$rating"}
            }
        },
        {
            "$sort": {"revenu_total": -1}  # Tri par revenu décroissant
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    print("\n=== Performance par région ===")
    for region in results:
        print(f"\nRégion: {region['_id']}")
        print(f"  Nombre de livraisons: {region['nb_livraisons']}")
        print(f"  Revenu total: {region['revenu_total']}€")
        print(f"  Durée moyenne: {region['duree_moyenne']:.1f} minutes")
        print(f"  Rating moyen: {region['rating_moyen']:.2f}/5")
    
    return results

# ===== TRAVAIL 4 : Agrégation avancée - Top livreurs =====
def get_top_drivers(limit=2):
    """Affiche le top des livreurs par revenu"""
    collection = get_deliveries_collection()
    
    pipeline = [
        {
            "$group": {
                "_id": {
                    "driver_id": "$driver_id",
                    "driver_name": "$driver_name"
                },
                "nb_livraisons": {"$sum": 1},
                "revenu_total": {"$sum": "$amount"},
                "duree_moyenne": {"$avg": "$duration_minutes"},
                "rating_moyen": {"$avg": "$rating"}
            }
        },
        {
            "$sort": {"revenu_total": -1}  # Tri par revenu décroissant
        },
        {
            "$limit": limit
        }
    ]
    
    results = list(collection.aggregate(pipeline))
    
    print(f"\n=== Top {limit} livreurs (par revenu) ===")
    for i, driver in enumerate(results, 1):
        print(f"\n{i}. {driver['_id']['driver_name']} ({driver['_id']['driver_id']})")
        print(f"   Livraisons: {driver['nb_livraisons']}")
        print(f"   Revenu total: {driver['revenu_total']}€")
        print(f"   Durée moyenne: {driver['duree_moyenne']:.1f} min")
        print(f"   Rating moyen: {driver['rating_moyen']:.2f}/5")
    
    return results

# ===== TRAVAIL 5 : Gestion des données - Indexation =====
def create_indexes():
    """Crée les index pour optimiser les performances"""
    collection = get_deliveries_collection()
    
    # Index simple sur driver_id
    index1 = collection.create_index("driver_id")
    print(f"\n✓ Index créé sur 'driver_id': {index1}")
    
    # Index composé sur region + delivery_time
    index2 = collection.create_index([("region", 1), ("delivery_time", 1)])
    print(f"✓ Index composé créé sur 'region' + 'delivery_time': {index2}")
    
    # Afficher tous les index
    print("\n=== Index existants ===")
    for index in collection.list_indexes():
        print(f"  • {index['name']}: {index['key']}")
    
    return [index1, index2]

def explain_indexes():
    """Explique l'utilité des index créés"""
    print("\n=== Explication des index ===")
    print("\n1. Index sur 'driver_id':")
    print("   • Accélère les requêtes de type find({'driver_id': 'd1'})")
    print("   • Utile pour le Travail 2 (historique d'un livreur)")
    print("   • Évite le scan complet de la collection")
    print("   • Complexité: O(log n) au lieu de O(n)")
    
    print("\n2. Index composé sur 'region' + 'delivery_time':")
    print("   • Accélère les requêtes filtrant sur la région ET/OU la date")
    print("   • Utile pour les analyses régionales par période")
    print("   • Permet de faire des requêtes comme:")
    print("     - find({'region': 'Paris'})")
    print("     - find({'region': 'Paris', 'delivery_time': {$gte: date}})")
    print("   • L'ordre (region, delivery_time) optimise les requêtes sur region seule")

# ===== TRAVAIL 6 : Synchronisation Redis → MongoDB (Bonus) =====
def sync_completed_delivery(delivery_data):
    """
    Insère une livraison complétée depuis Redis vers MongoDB
    
    Args:
        delivery_data (dict): Dictionnaire contenant les données de la livraison
    """
    collection = get_deliveries_collection()
    
    # Insérer le document
    result = collection.insert_one(delivery_data)
    print(f"✓ Livraison {delivery_data['command_id']} synchronisée dans MongoDB (ID: {result.inserted_id})")
    
    return result.inserted_id

def explain_sync_logic():
    """Explique la logique de synchronisation Redis → MongoDB"""
    print("\n=== Logique de synchronisation Redis → MongoDB ===")
    print("\n1. Quand une livraison se termine dans Redis:")
    print("   • Événement déclenché: statut passe à 'livrée'")
    print("   • Récupérer toutes les infos depuis Redis (commande + livreur)")
    
    print("\n2. Construction du document MongoDB:")
    print("   • command_id, client, driver_id, driver_name")
    print("   • pickup_time, delivery_time, duration_minutes")
    print("   • amount, region, rating, review, status")
    
    print("\n3. Appel de sync_completed_delivery():")
    print("   • Insère le document dans MongoDB")
    print("   • Permet de garder l'historique permanent")
    
    print("\n4. Avantages:")
    print("   • Redis = temps réel (rapide, volatile)")
    print("   • MongoDB = historique + analyses (persistant)")
    print("   • Meilleure séparation des responsabilités")

# ===== MENU PRINCIPAL =====
def main():
    """Menu principal pour tester tous les travaux"""
    print("=" * 60)
    print("PARTIE 2 : Historique et Analyses avec MongoDB")
    print("=" * 60)
    
    try:
        # Travail 1
        print("\n--- TRAVAIL 1 : Importer l'historique ---")
        import_initial_history()
        
        # Travail 2
        print("\n--- TRAVAIL 2 : Historique d'un livreur ---")
        get_driver_history("d1")
        get_driver_stats("d1")
        
        # Travail 3
        print("\n--- TRAVAIL 3 : Performance par région ---")
        get_region_performance()
        
        # Travail 4
        print("\n--- TRAVAIL 4 : Top livreurs ---")
        get_top_drivers(2)
        
        # Travail 5
        print("\n--- TRAVAIL 5 : Gestion des index ---")
        create_indexes()
        explain_indexes()
        
        # Travail 6
        print("\n--- TRAVAIL 6 : Synchronisation Redis → MongoDB ---")
        explain_sync_logic()
        
        print("\n" + "=" * 60)
        print("✓ Tous les travaux de la Partie 2 sont terminés!")
        print("✓ Vérifie dans MongoDB Compass pour voir les données")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
